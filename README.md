# py-anime_dl
Funciones para descarga de series de anime, de distintos servidores

## **Requerimientos**
Para instalar las dependencias necesarias se debe instalar los paquetes indicados en _requeriments.txt_

``
  pip install -r requeriments.txt
``

## **Uso**
```python
import scrappers
#para usar scraper animeyt
anm = scrappers.get_animeyt_scrapper()
#buscar
resultados = anm.buscar('dragon ball')
#descargar primer elemento de resultado, a partir del capitulo 20
anm.descargar(resultados[0], 20)
```

## **Paginas soportadas**

* [animeyt](animeyt.net)
* [animeflv](animeflv.me)
