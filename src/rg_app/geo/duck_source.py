import duckdb


def create_db(json_dir: str):
    conn = duckdb.connect("data/geo.db")
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.sql("""
             DROP TABLE IF EXISTS borders
             """)

    conn.sql("""
    CREATE TABLE borders (
        ID VARCHAR PRIMARY KEY,
        shape GEOMETRY,
        type VARCHAR,
        parent_id VARCHAR NULL
    )""")

    # conn.sql("""
    # ALTER TABLE borders
    #     ADD CONSTRAINT fk_parent
    #     FOREIGN KEY (parent_id) REFERENCES borders(ID);
    #          """)

    communes_json = f"{json_dir}/A03_Granice_gmin.json"
    conn.sql(
        f"""INSERT INTO borders
        SELECT 
            CONCAT('PL', LPAD(CAST(JPT_KOD_JE AS VARCHAR), 7, '0')) as ID,
            geom AS shape, 
            JPT_SJR_KO as type,
            NULL as parent_id
        FROM ST_Read('{communes_json}')"""
    )

    counties_json = f"{json_dir}/A02_Granice_powiatow.json"
    conn.sql(
        f"""INSERT INTO borders
        SELECT 
            CONCAT('PL', LPAD(CAST(JPT_KOD_JE AS VARCHAR), 4, '0')) as ID,
            geom AS shape,
            JPT_SJR_KO as type,
            NULL as parent_id
        FROM ST_Read('{counties_json}')"""
    )

    voivodeships_json = f"{json_dir}/A01_Granice_wojewodztw.json"
    conn.sql(
        f"""INSERT INTO borders
        SELECT 
            CONCAT('PL', LPAD(CAST(JPT_KOD_JE AS VARCHAR), 2, '0')) as ID,
            geom AS shape,
            JPT_SJR_KO as type,
            NULL as parent_id
        FROM ST_Read('{voivodeships_json}')"""
    )

    country_json = f"{json_dir}/A00_Granice_panstwa.json"
    conn.sql(
        f"""INSERT INTO borders
        SELECT 
            'PL' as ID,
            geom AS shape,
            JPT_SJR_KO as type,
            NULL as parent_id
        FROM ST_Read('{country_json}')"""
    )

    conn.sql("""
    UPDATE borders
    SET parent_id = 'PL'
    WHERE type = 'WOJ'
    """)

    conn.sql("""
    UPDATE borders
    SET parent_id = substr(ID, 1, 4)
    WHERE type = 'POW'
    """)

    conn.sql("""
    UPDATE borders
    SET parent_id = substr(ID, 1, 6)
    WHERE type = 'POW'
    """)


#     WITH shp as (
# SELECT
#   name, geom AS geom
# FROM ST_Read('~/Downloads/output2.shp/tracks.shp')
# )
# SELECT borders.ID, borders.type , ST_AsGeoJSON(borders.shape), ST_AsGeoJSON(geom)
# FROM borders
# INNER JOIN shp ON ST_Intersects(shape, geom)


if __name__ == "__main__":
    create_db("data/gml")
