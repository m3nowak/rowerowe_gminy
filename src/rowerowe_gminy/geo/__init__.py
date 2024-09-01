import logging
import os
import os.path
import typing

import geopandas

import rowerowe_gminy.core


def load_gml_files(src_dir: str) -> typing.Dict[str, geopandas.GeoDataFrame]:
    types = [
        rowerowe_gminy.core.COUNTRY_FNAME,
        rowerowe_gminy.core.VOIVODESHIPS_FNAME,
        rowerowe_gminy.core.COUNTIES_FNAME,
        rowerowe_gminy.core.COMMUNES_FNAME,
    ]
    prefixes = ["A00", "A01", "A02", "A03"]
    ext = ".gml"

    dir_contents = os.listdir(src_dir)
    print(dir_contents)
    result = {}

    for prefix, fctype in zip(prefixes, types):
        dir_contents_suitable = [f for f in dir_contents if f.startswith(prefix) and f.endswith(ext)]
        assert (
            len(dir_contents_suitable) == 1
        ), f"Expected 1 file with prefix {prefix} and extension {ext}, got {len(dir_contents_suitable)}"
        path = os.path.join(src_dir, dir_contents_suitable[0])
        result[fctype] = geopandas.read_file(path)
    return result


def reformat_metadata(fc: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    fc["TERYT"] = fc["JPT_KOD_JE"].astype(str)
    fc["name"] = fc["JPT_NAZWA_"]
    fc["type"] = fc["JPT_SJR_KO"]
    to_drop = fc.columns.difference(["geometry", "TERYT", "name", "type"])
    fc = fc.drop(columns=to_drop)
    max_teryt_len = fc["TERYT"].str.len().max()
    fc["TERYT"] = fc["TERYT"].str.zfill(max_teryt_len)
    fc.set_index("TERYT", inplace=True)
    return fc


def simplify_geometry(fc: geopandas.GeoDataFrame, acc: float) -> geopandas.GeoDataFrame:
    fc.geometry = fc.geometry.simplify(acc)
    return fc


def reformat_dataset(src_dir: str, dst_dir: str):
    # types = [rowerowe_gminy.core.VOIVODESHIPS_FNAME, rowerowe_gminy.core.COUNTIES_FNAME, rowerowe_gminy.core.COMMUNES_FNAME, rowerowe_gminy.core.COUNTRY_FNAME]
    gdf_dict = load_gml_files(src_dir)
    for fctype, gdf in gdf_dict.items():
        gdf = simplify_geometry(gdf, 25)
        gdf.geometry = gdf.geometry.to_crs(crs="EPSG:4326")
        gdf = reformat_metadata(gdf)
        dst_path = os.path.join(dst_dir, f"{fctype}.json")
        gdf.to_file(dst_path, driver="GeoJSON")


def main():
    logging.basicConfig(level=logging.INFO)
    reformat_dataset("./data/gml/", "./data/geojsonfixedlite/")


if __name__ == "__main__":
    main()
