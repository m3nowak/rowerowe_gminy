from rg_app.geo.simplification import toposimplify_duckdb

# from rg_app.geo.src_load import load_gml_files

if __name__ == "__main__":
    duck_path = "data/geo.db"
    sb500 = toposimplify_duckdb(duck_path, 0.002)
    sb200 = toposimplify_duckdb(duck_path, 0.005)
    # sb500.to_file("data/dgs2e_3.json", driver="GeoJSON")
    # sb100.to_file("data/dgs1e_2.json", driver="GeoJSON")
    # sb500.to_file("data/dgs2e_3.topojson", driver="GeoJSON")
    # sb100.to_file("data/dgs1e_2.topojson", driver="GeoJSON")
