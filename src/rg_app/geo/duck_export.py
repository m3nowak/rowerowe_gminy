import duckdb


def pg_export(pg_connstr: str, db_path: str | None = None) -> None:
    db_path = db_path or "data/geo.db"
    conn = duckdb.connect(db_path)
    conn.load_extension("postgres")
    conn.load_extension("spatial")
    conn.execute(
        f"ATTACH '{pg_connstr}' as pdb (TYPE POSTGRES, SCHEMA public)",
    )

    conn.execute("""
                DELETE FROM pdb.region
                """)

    conn.execute("""
                INSERT INTO pdb.region
                SELECT ID as id, type as type, ancestors as ancestors FROM borders
                """)


if __name__ == "__main__":
    pg_export("dbname=postgres host=localhost user=postgres password=postgres")
