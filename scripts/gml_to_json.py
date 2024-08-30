# gml_to_json.py
# /// script
# requires-python = ">=3.12"
# dependencies = [
# ]
# ///

import os.path
import shutil
import subprocess

MAPPING = {
    "./data/gml/A00_Granice_panstwa.gml": "./data/json/country.json",
    "./data/gml/A01_Granice_wojewodztw.gml": "./data/json/voivodeships.json",
    "./data/gml/A02_Granice_powiatow.gml": "./data/json/counties.json",
    "./data/gml/A03_Granice_gmin.gml": "./data/json/communes.json",
}

COMMAND_TEMPLATE = "ogr2ogr -f GeoJSON -s_srs EPSG:2180 -t_srs EPSG:4326 {dst_fname} {src_fname}"

assert (
    shutil.which("ogr2ogr") is not None
), 'ogr2ogr command not found (get "gdal" package at https://gdal.org/en/latest/download.html)'

for src_fname in MAPPING:
    assert os.path.exists(src_fname), f"File {src_fname} not found"

shutil.rmtree("./data/json/", ignore_errors=True)
os.makedirs("./data/json/", exist_ok=True)

processes = []
for src_fname, dst_fname in MAPPING.items():
    command = COMMAND_TEMPLATE.format(src_fname=src_fname, dst_fname=dst_fname)
    print(command)
    processes.append(subprocess.Popen(command, shell=True))

for p in processes:
    p.wait()

print("Done")
