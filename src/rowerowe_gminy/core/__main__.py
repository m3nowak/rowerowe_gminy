import pygml
from lxml import etree
import contextlib

def main():
    with contextlib.closing(open('data/gml/A00_Granice_panstwa.gml', 'r')) as f:
        el = etree.parse(f) # type: ignore
        pygml.parse(el)
        print('Hello from rowerowe_gminy!')

if __name__ == '__main__':
    main()