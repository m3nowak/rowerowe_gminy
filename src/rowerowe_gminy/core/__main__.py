import contextlib

import pygml
from lxml import etree


def fix_polygon(polygon_element):
    new_polygon = etree.Element("{http://www.opengis.net/gml}Polygon")  # type: ignore
    for ring in polygon_element.iterfind(".//{http://www.opengis.net/gml}LinearRing"):
        new_polygon.append(ring)
    return new_polygon


def main():
    tgt = []
    with contextlib.closing(open("data/gml/A00_Granice_panstwa.gml", "rb")) as f:
        tree = etree.fromstring(f.read())  # type: ignore
        # change namespace 'http://www.opengis.net/gml' to 'http://www.opengis.net/gml'

        for feature_member in tree.iterfind(".//{http://www.opengis.net/gml}Polygon"):
            fixed_polygon = fix_polygon(feature_member)
            tgt.append(pygml.parse(fixed_polygon))
    print(tgt)


if __name__ == "__main__":
    main()
