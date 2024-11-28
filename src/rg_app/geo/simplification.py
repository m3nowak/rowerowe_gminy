import typing as ty

import duckdb
import geopandas as gpd
import topojson as tp


def toposimplify_duckdb(path: str, toposimplify: float) -> str:
    """Create a topology to ensure proper boundaries between regions and simplify it."""
    # shamelessly stolen from https://github.com/kraina-ai/srai/blob/main/srai%2Fregionalizers%2Fadministrative_boundary_regionalizer.py#L313-L332
    with duckdb.connect(path) as conn:
        conn.load_extension("spatial")

        df = conn.execute(
            "SELECT borders.ID , ST_AsText(borders.shape) as shape, type, parent_id FROM borders WHERE type='GMI'"  # WHERE type='WOJ' OR type='PAN'
        ).df()

        gdf = gpd.GeoDataFrame(data=df, geometry=gpd.GeoSeries.from_wkt(df["shape"]), crs="EPSG:4326")  # type: ignore

        gdf.drop(columns=["shape"], inplace=True)

        topo = tp.Topology(
            gdf,
            prequantize=1e6,  # type: ignore
            presimplify=False,
            toposimplify=toposimplify,  # type: ignore
            simplify_algorithm="dp",
            prevent_oversimplify=True,
        )
        return ty.cast(str, topo.to_json())
