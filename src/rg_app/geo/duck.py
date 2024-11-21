import duckdb
from geopandas import GeoDataFrame


def create_conn(gdf: GeoDataFrame) -> duckdb.DuckDBPyConnection:
    # Convert GeoDataFrame to plain DataFrame with GeoJSON geometry
    df = gdf.copy()
    df["geometry"] = df.geometry.apply(lambda x: x.__geo_interface__)

    # Create connection and register DataFrame
    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    conn.register("geo", df)
    return conn
