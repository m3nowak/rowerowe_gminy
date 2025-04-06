import duckdb


def pg_export(pg_url: str, db_path: str | None = None) -> None:
    try:
        import psycopg as _  # noqa
        import sqlalchemy as sa
        from sqlalchemy.dialects.postgresql import insert
        from rg_app.db import Region
    except ImportError:
        raise ImportError(
            "This command requires sqlalchemy and psycopg, install oprional dependencies named db (rg-app[db])"
        )
    db_path = db_path or "data/geo.db"
    conn = duckdb.connect(db_path, read_only=True)
    conn.install_extension("postgres")
    conn.install_extension("spatial")
    conn.load_extension("postgres")
    conn.load_extension("spatial")
    # Below won't work due to DuckDB not recognizing ON CONFLICT and postgresql primary keys
    # conn.execute("""
    #         INSERT INTO pdb.region
    #         (SELECT ID as id, type as type, ancestors as ancestors FROM borders)
    #         ON CONFLICT (id) DO UPDATE
    #         SET type = EXCLUDED.type,
    #             ancestors = EXCLUDED.ancestors
    #         """)

    # Get all regions from DuckDB
    regions = conn.execute("SELECT ID as id, type, ancestors, name FROM borders").fetchall()

    engine = sa.create_engine(pg_url)

    with engine.connect() as pg_conn:
        for region in regions:
            insert_stmt = (
                insert(Region)
                .values(id=region[0], type=region[1], ancestors=region[2], name=region[3])
                .on_conflict_do_update(
                    index_elements=[Region.id],
                    set_={"type": region[1], "ancestors": region[2], "name": region[3]},
                )
            )
            pg_conn.execute(insert_stmt)
        pg_conn.commit()


if __name__ == "__main__":
    pg_export("postgres+psycopg://postgres:postgres@localhost/postgres")
    # pg_export("dbname=postgres host=localhost user=postgres password=postgres")
