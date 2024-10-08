# download_gml.py
# /// script
# requires-python = ">=3.12"
# dependencies = [
# ]
# ///
"""Download GML file from url"""

import os.path
import shutil
import urllib.request
import zipfile

LOCAL_ZIP_PATH = "data/gml_pak.zip"
URL = "https://opendata.geoportal.gov.pl/prg/granice/00_jednostki_administracyjne_gml.zip"
URL2 = "https://opendata.geoportal.gov.pl/prg/adresy/PRG-punkty_adresowe.zip"

if not os.path.exists(LOCAL_ZIP_PATH):
    urllib.request.urlretrieve(URL, "data/gml_pak.zip")

shutil.rmtree("data/gml", ignore_errors=True)

with zipfile.ZipFile("data/gml_pak.zip", "r") as zip_ref:
    zip_ref.extractall("data/gml")
