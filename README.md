# rowerowe_gminy

konwersja:
```ogr2ogr -f GeoJSON -s_srs EPSG:2180 -t_srs EPSG:4326 ./data/json/panstwo.json data/gml/A00_Granice_panstwa.gml```