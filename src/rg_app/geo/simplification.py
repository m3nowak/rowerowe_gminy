import geopandas as gpd
import topojson as tp
from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid

from rg_app.core import REGIONS_INDEX

TARGET_CRS = "EPSG:4326"
SOURCE_CRS = "EPSG:2180"


def toposimplify_gdf(regions_gdf: gpd.GeoDataFrame, toposimplify: float) -> gpd.GeoDataFrame:
    """Create a topology to ensure proper boundaries between regions and simplify it."""
    # shamelessly stolen from https://github.com/kraina-ai/srai/blob/main/srai%2Fregionalizers%2Fadministrative_boundary_regionalizer.py#L313-L332
    topo = tp.Topology(
        regions_gdf,
        prequantize=1e6, # type: ignore
        presimplify=False,
        toposimplify=toposimplify,  # type: ignore
        simplify_algorithm="dp",
        prevent_oversimplify=True,
    )
    regions_gdf = topo.to_gdf(winding_order="CW_CCW", crs=TARGET_CRS, validate=True)
    # fix crs
    regions_gdf.geometry.set_crs(crs=SOURCE_CRS, inplace=True, allow_override=True)
    regions_gdf.geometry = regions_gdf.geometry.to_crs(crs=TARGET_CRS)
    # index rename
    regions_gdf.index.rename(REGIONS_INDEX, inplace=True)

    return regions_gdf
