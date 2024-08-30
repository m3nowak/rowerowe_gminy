import geojson
import logging
import os.path
import rowerowe_gminy.core

def load_fc(file_path: str) -> geojson.FeatureCollection:
    with open(file_path) as f:
        fc = geojson.load(f)
    assert isinstance(fc, geojson.FeatureCollection)
    return fc

def save_fc(fc: geojson.FeatureCollection, file_path: str):
    with open(file_path, "w") as f:
        geojson.dump(fc, f)

def reformat_metadata(fc: geojson.FeatureCollection) -> geojson.FeatureCollection:
    for feature in fc.features:
        if "fid" in dict(feature.properties):
            final_properties = {}
            final_properties["TERYT"] = feature.properties.get("JPT_KOD_JE")
            final_properties["name"] = feature.properties.get("JPT_NAZWA_")
            final_properties["type"] = feature.properties.get("JPT_SJR_KO")
            feature.properties = final_properties
        else:
            logging.info("Metadata reformatting already done")
    return fc

def reformat_dataset(src_dir: str, dst_dir: str):
    types = [rowerowe_gminy.core.VOIVODESHIPS_FNAME, rowerowe_gminy.core.COUNTIES_FNAME, rowerowe_gminy.core.COMMUNES_FNAME]
    for fctype in types:
        src_path = os.path.join(src_dir, f"{fctype}.json")
        dst_path = os.path.join(dst_dir, f"{fctype}.json")
        fc = load_fc(src_path)
        fc = reformat_metadata(fc)
        save_fc(fc, dst_path)
        logging.info(f"Reformatted {fctype}, features: {len(fc.features)}")

def main():
    logging.basicConfig(level=logging.INFO)
    reformat_dataset("./data/geojson/", "./data/geojsonfixed/")

if __name__ == "__main__":
    main()