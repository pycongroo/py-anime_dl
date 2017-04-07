# -*- coding: utf-8 -*-
import os
import re
import time
from bs4 import BeautifulSoup as Bs
import cfscrape as cfs
import externos.pynet.pynet as net
import externos.pynet.modules.colors as clrs

default_download_path = 'descargas'

class Scraper():
    cache = {}
    sesion = None
    base_link = ''
    scraper_name = ''
    dl_path = ''

    def __init__(self, base_path):
        self.dl_path = base_path + '/'
        self.dl_path += self.scraper_name + '/'
        self.sesion = net.NetHandler(cfs.create_scraper())
        self.preparar_antibot_cf()

    def preparar_antibot_cf(self):
        clrs.m_aviso('Preparando contra CloudFlare...')
        inicial = time.clock()
        hreq = self.sesion.request_get(self.base_link)
        final = time.clock()
        clrs.m_aviso("Se tardó %s segundos" % str(round((final-inicial)*10000)))
        if (hreq.status_code==200):
            clrs.m_aviso('Completado')
        else:
            m_aviso('ocurrio un problema')

    def buscar_en_cache(self, criterio):
        return self.cache.get(criterio)

    def buscar(self, criterio):
        resultados = self.buscar_en_cache(criterio)
        if (resultados is None):
            url = self.url_busqueda(criterio)
            resultados = self.get_results_from_url(url)
            self.cache.update({criterio:resultados})
        return resultados

    def descargar(self, serie, desde=None):
        self.create_if_not_exists(self.dl_path.split('/')[0])
        self.create_if_not_exists(self.dl_path)
        serie_path = self.dl_path + serie['title'] + '/'
        self.create_if_not_exists(serie_path)
        capitulos_totales = self.get_capitulos_from_url(serie['link'])
        if (desde is None):
            capitulos = capitulos_totales
        else:
            if (desde >= len(capitulos_totales)):
                clrs.m_aviso("seleccion no disponible")
            capitulos =  capitulos_totales[desde-1:]
        for capitulo in capitulos:
            self.descargar_capitulo(capitulo, serie_path)

    def descargar_capitulo(self, capitulo, dir_path):
        path_capitulo = dir_path + capitulo['title'] + '.mp4'
        if os.path.exists(path_capitulo):
            clrs.m_aviso("Ya existe %s" % path_capitulo)
        else:
            cap_dl_link = self.get_download_link_from_url(capitulo['link'])
            try:
                clrs.m_aviso("using native wget")
                status = os.system('wget -O "%s" "%s"' % (path_capitulo, cap_dl_link))
                if (status != 0):
                    print status
                    clrs.m_interr('\nCancelado wget')
                    os.system('rm "%s"' % path_capitulo)
                if (status == 2048):
                    clrs.m_aviso("Wget failed")
                    0/0
            except Exception as e:
                clrs.m_aviso("Wget failed")
                clrs.m_aviso("Trying requests package mode")
                self.sesion.download_file(cap_dl_link, path_capitulo)

    def create_if_not_exists(self, dir_path):
        if os.path.exists(dir_path):
            clrs.m_aviso("Ya existe %s" % dir_path)
        else:
            clrs.m_aviso("No existe %s" % dir_path)
            os.mkdir(dir_path)

class AnimeytScraper(Scraper):
    base_link = 'http://www.animeyt.tv/'
    scraper_name = 'animeyt'
    re_link_js = re.compile('.*url = \"(.*?)\";.*')

    ##metodos de busqueda
    def url_busqueda(self, criterio):
        busqueda_prev = '%sbusqueda' % self.base_link
        return '%s?terminos=%s' % (busqueda_prev, criterio.replace(' ', '+'))

    def get_results_from_url(self, url):
        sreq = self.sesion.request_get(url)
        s_text = Bs(sreq.text, 'lxml')
        l_anime_divs = s_text.findAll('article', {'class': 'anime'})
        l_d_animes = map(self.get_anime_from_div, l_anime_divs)
        return l_d_animes

    def get_anime_from_div(self, anime_div):
        d_anime = {}
        d_anime.update({'title': self.get_title(anime_div)})
        d_anime.update({'poster': self.get_poster_link(anime_div)})
        d_anime.update({'synopsis': self.get_synopsis(anime_div)})
        d_anime.update({'link': self.get_link(anime_div)})
        d_anime.update({'date': self.get_date(anime_div)})
        d_anime.update({'status': self.get_status(anime_div)})
        d_anime.update({'genres': self.get_genres(anime_div)})
        d_anime.update({'tags': self.get_tags(anime_div)})
        return d_anime

    def get_poster_link(self, anime_div):
        poster_link = anime_div.find('img', {'class': 'anime__img'}).get('src')
        return poster_link

    def get_title(self, anime_div):
        anime_title = anime_div.find('h3', {'class': 'anime__title'}).getText()
        return anime_title

    def get_synopsis(self, anime_div):
        anime_synopsis = anime_div.find(
            'p', {'class': 'anime__synopsis js-synopsis-reduce'}).getText()
        return anime_synopsis

    def get_link(self, anime_div):
        anime_link = anime_div.find('a', {'anime__synopsis-container'}).get('href')
        return anime_link

    def get_date(self, anime_div):
        anime_date = anime_div.find('span', {'class': 'icon-fecha'}).getText()
        return anime_date

    def get_status(self, anime_div):
        anime_status = anime_div.find('span', {'class': 'anime__status'}).getText()
        return anime_status

    def get_genres(self, anime_div):
        l_span_genre = anime_div.findAll('span', {'class': 'anime__genre'})
        l_genres = map(self.get_genre, l_span_genre)
        return l_genres

    def get_genre(self, genre_span):
        genre = genre_span.getText()
        return genre

    def get_tags(self, anime_div):
        l_span_tag = anime_div.findAll('span', {'class': 'anime__tag'})
        l_tags = map(self.get_tag, l_span_tag)
        return l_tags

    def get_tag(self, tag_span):
        tag = tag_span.getText()
        return tag

    #scrapping de obtencion de capitulos
    def get_capitulos_from_url(self, url_serie):
        creq = self.sesion.request_get(url_serie)
        c_text = Bs(creq.text, 'lxml')
        l_chapters = c_text.findAll(
        'div', {'class': 'serie-capitulos__list__item'})
        l_d_chapters = map(self.get_chapter_from_div, l_chapters)
        l_d_chapters.reverse()
        return l_d_chapters

    def get_chapter_from_div(self, chapter_div):
        d_chapter = {}
        d_chapter.update({'title': self.get_chapter_title(chapter_div)})
        d_chapter.update({'link': self.get_chapter_link(chapter_div)})
        return d_chapter


    def get_chapter_title(self, chapter_div):
        chapter_title = chapter_div.find('a').getText().replace('\n', ' ')
        return chapter_title


    def get_chapter_link(self, chapter_div):
        chapter_link = chapter_div.find('a').get('href')
        return chapter_link

    #scrapping de obtencion de links de descarga de capitulo
    def get_download_link_from_url(self, url_capitulo):
        c_req = self.sesion.request_get(url_capitulo)
        c_text = Bs(c_req.text, 'lxml')
        download_url_redir = c_text.find(
            'a', {'target': '_blank'}, text='Descarga').get('href')
        ## ubico enlace generado de descarga
        download_url = self.get_link_by_link_page(download_url_redir)
        return download_url

    def get_link_by_link_page(self, dl_link):
        b_text = Bs(self.sesion.request_get(dl_link).text, 'lxml')
        script_tag = b_text.findAll('script')[1]
        text_url = script_tag.string.split('\n')[8]
        url_real = self.re_link_js.match(text_url).groups()[0]
        return url_real

class AnimeflvScraper(Scraper):
    base_link = 'http://www.animeflv.me/'
    scraper_name = 'animeflv-me'
    re_link_url_js = re.compile('https://\S*')
    res=None

    def __init__(self, base_path, res=None):
        Scraper.__init__(self, base_path)
        if res is None:
            clrs.m_aviso("resolucion no ingresada, tomara 480p")
            self.res = 1
        else:
            self.res = res

    ##metodos de busqueda
    def url_busqueda(self, criterio):
        busqueda_prev = '%sBuscar' % self.base_link
        return '%s?s=%s' % (busqueda_prev, criterio.replace(' ', '+'))

    def get_results_from_url(self, url):
        sreq = self.sesion.request_get(url)
        if (sreq.url==url):
            l_d_anime = self.get_animes_from_html(sreq.text)
        else:
            b_text = Bs(sreq.text, 'lxml')
            #if (b_text.findAll('tr')[0].find('th').getText()==' Anime'):
            d_anime = {}
            d_anime.update({'title':b_text.find('a',{'class':'bigChar'}).getText().replace('  ','').replace('\n','')})
            d_anime.update({'link': sreq.url})
            l_d_anime=[d_anime]
        return l_d_anime

    def get_animes_from_html(self, h_text):
        b_text = Bs(h_text, 'lxml')
        l_anime_divs = b_text.findAll('tr')[2:]
        l_d_animes = map(self.get_anime_from_div, l_anime_divs)
        return l_d_animes

    def get_anime_from_div(self, anime_div):
        d_anime = {}
        anime_upd = anime_div.find('td')
        d_anime.update({'title': self.get_title(anime_upd)})
        #d_anime.update({'poster': get_poster_link(anime_upd)})
        #d_anime.update({'synopsis': get_synopsis(anime_upd)})
        d_anime.update({'link': self.get_link(anime_upd)})
        #d_anime.update({'date': get_date(anime_upd)})
        #d_anime.update({'status': self.get_status(anime_upd)})
        #d_anime.update({'genres': get_genres(anime_upd)})
        #d_anime.update({'tags': get_tags(anime_upd)})
        return d_anime

    def get_title(self, anime_div):
        anime_title = anime_div.find('a').getText().split('\r')[0].replace('\n', ' ')
        return anime_title

    def get_link(self, anime_div):
        anime_link = anime_div.find('a').get('href')
        return anime_link

    # scrapping de obtencion de capitulos
    def get_capitulos_from_url(self, url_serie):
        creq = self.sesion.request_get(url_serie)
        c_text = Bs(creq.text, 'lxml')
        l_chapters = c_text.findAll('tr')[2:]
        l_d_chapters = map(self.get_chapter_from_div, l_chapters)
        l_d_chapters.reverse()
        return l_d_chapters

    def get_chapter_from_div(self, chapter_div):
        d_chapter = {}
        chapter_adp=chapter_div.find('td')
        d_chapter.update({'title': self.get_chapter_title(chapter_adp)})
        d_chapter.update({'link': self.get_chapter_link(chapter_adp)})
        return d_chapter


    def get_chapter_title(self, chapter_div):
        chapter_title = chapter_div.find('a').getText().split('\r')[0].replace('\n', ' ').replace('   ','')
        return chapter_title


    def get_chapter_link(self, chapter_div):
        chapter_link = chapter_div.find('a').get('href')
        return chapter_link

    #scrapping de obtencion de links de descarga de capitulo
    def get_download_link_from_url(self, url_capitulo):
        c_req = self.sesion.request_get(url_capitulo)
        c_text = Bs(c_req.text, 'lxml')
        download_url_redir = c_text.find('iframe').get('src')
        ## ubico enlace generado de descarga
        download_url = self.get_link_by_link_page(download_url_redir)
        return download_url

    def get_link_by_link_page(self, dl_link):
        ##recibe url de player.animeflv
        b_text = Bs(self.sesion.request_get(dl_link).text, 'lxml')
        #url_real = b_text.find('video').find('source').get('src')
        links_str_list=b_text.findAll('script')[7].getText().split('[')[1].split(']')[0].split('"')
        #es una lista con los enlaces y basura, debe ser filtrado
        #for i in links_res:
        #    print i
        #time.sleep()
        links_res=filter(self.re_link_url_js.match,links_str_list)
        #if (res>=len(links_res)):
        #    clrs.m_aviso('resolucion no encontrada, tomando 480p(1)')
        #    res=1
        #return url_real
        return links_res[self.res]

def get_animeyt_scrapper():
    return AnimeytScraper(default_download_path)

def get_animeflv_scrapper(res=None):
    return AnimeflvScraper(default_download_path, res)
