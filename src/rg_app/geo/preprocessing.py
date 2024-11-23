import geopandas

TARGET_CRS = "EPSG:4326"
SOURCE_CRS = "EPSG:2180"


def preprocess_gml(path: str) -> None:
    """Preprocess GML file."""
    gdf = geopandas.read_file(path)
    gdf.geometry.set_crs(crs=SOURCE_CRS, inplace=True, allow_override=True)
    gdf.geometry = gdf.geometry.to_crs(crs=TARGET_CRS)

    if path.endswith(".gml"):
        target_path = path[:-4] + ".json"
    else:
        target_path = path + ".json"

    gdf.to_file(target_path, driver="GeoJSON")


if __name__ == "__main__":
    import sys

    preprocess_gml(sys.argv[1])
