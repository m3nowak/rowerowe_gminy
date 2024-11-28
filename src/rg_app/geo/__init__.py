import gzip

from rg_app.geo.simplification import toposimplify_duckdb

# from rg_app.geo.src_load import load_gml_files

if __name__ == "__main__":
    duck_path = "data/geo.db"
    sb200 = toposimplify_duckdb(duck_path, 0.005)
    with open("data/tpy5e_3.json", "w") as f:
        f.write(sb200)
    with gzip.open("data/tpy5e_3.json.gz", "wt") as f:
        f.write(sb200)
