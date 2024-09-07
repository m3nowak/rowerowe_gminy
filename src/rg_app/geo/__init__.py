import rg_app.core

from rg_app.geo.src_load import load_gml_files
from rg_app.geo.simplification import toposimplify_gdf

if __name__ == "__main__":
    a = load_gml_files('data/gml')
    b = a.communes
    sb200 = toposimplify_gdf(b,200)
    sb500 = toposimplify_gdf(b,500)
    sb500.to_file('data/gs500.json', driver="GeoJSON")
    sb200.to_file('data/gs200.json', driver="GeoJSON")
    