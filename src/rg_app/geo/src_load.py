import logging
import os
import os.path
from dataclasses import dataclass

import geopandas
import pandas

import rg_app.core
from rg_app.core import REGIONS_INDEX


@dataclass
class GdfBundle:
    voivodeships: geopandas.GeoDataFrame
    counties: geopandas.GeoDataFrame
    communes: geopandas.GeoDataFrame
    country: geopandas.GeoDataFrame


def _reformat_metadata(fc: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    fc[REGIONS_INDEX] = fc["JPT_KOD_JE"].astype(str)
    fc["name"] = fc["JPT_NAZWA_"]
    fc["type"] = fc["JPT_SJR_KO"]
    to_drop = fc.columns.difference(["geometry", REGIONS_INDEX, "name", "type"])
    fc = fc.drop(columns=to_drop)  # type: ignore
    max_teryt_len = fc[REGIONS_INDEX].str.len().max()
    fc[REGIONS_INDEX] = fc[REGIONS_INDEX].str.zfill(max_teryt_len)
    fc.set_index(REGIONS_INDEX, inplace=True)
    return fc


# def _extend_region_data(fc: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
#     # fc["COU_ID"] = fc.index.str.slice(0, 4)
#     fc.loc[fc["type"] not in ["WOJ", "PAN"], "VOI_ID"] = fc.loc[fc["type"] not in ["WOJ", "PAN"]].index.str.slice(0, 4)

#     # Before: Sets VOI_ID for all rows
#     fc.loc[fc["type"] not in ["PAN"], "VOI_ID"] = fc.loc[fc["type"] not in ["PAN"]].index.str.slice(0, 2)
#     return fc


def _add_parent_id(fc: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    # PAN
    fc["parent_id"] = None
    # WOJ
    fc.loc[fc["type"] == "WOJ", "parent_id"] = 0  # type: ignore
    # POW
    fc.loc[fc["type"] == "POW", "parent_id"] = fc.loc[fc["type"] == "POW"].index.str.slice(0, 2)  # type: ignore
    # GMI
    fc.loc[fc["type"] == "GMI", "parent_id"] = fc.loc[fc["type"] == "GMI"].index.str.slice(0, 4)  # type: ignore
    return fc


def load_gml_files(src_dir: str) -> GdfBundle:
    types = [
        rg_app.core.COUNTRY_FNAME,
        rg_app.core.VOIVODESHIPS_FNAME,
        rg_app.core.COUNTIES_FNAME,
        rg_app.core.COMMUNES_FNAME,
    ]
    prefixes = ["A00", "A01", "A02", "A03"]
    ext = ".gml"

    dir_contents = os.listdir(src_dir)
    result = {}

    for prefix, fctype in zip(prefixes, types):
        dir_contents_suitable = [f for f in dir_contents if f.startswith(prefix) and f.endswith(ext)]
        assert (
            len(dir_contents_suitable) == 1
        ), f"Expected 1 file with prefix {prefix} and extension {ext}, got {len(dir_contents_suitable)}"
        path = os.path.join(src_dir, dir_contents_suitable[0])
        result[fctype] = _add_parent_id(_reformat_metadata(geopandas.read_file(path)))

    return GdfBundle(**result)


def bundle_to_combo(bundle: GdfBundle) -> geopandas.GeoDataFrame:
    return geopandas.GeoDataFrame(
        pandas.concat([bundle.voivodeships, bundle.counties, bundle.communes, bundle.country])
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bundle = load_gml_files("data/gml")
    combo = bundle_to_combo(bundle)
    combo.to_file("data/rg_app_combo.gpkg", driver="GPKG")
    logging.info("Saved combo to data/rg_app_combo.gpkg")
