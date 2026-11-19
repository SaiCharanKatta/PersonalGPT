"""Import a verified SQLite backup into a new private PostgreSQL schema."""

from contextlib import closing
from hashlib import sha256
from pathlib import Path
import argparse
import os
import sqlite3

from psycopg import sql

from postgres_backend import SCHEMA, postgres_schema, raw_connection


def migrate(backup, dsn):
    source = (backup / "personal_gpt.db").resolve(strict=True)
    uploads = (backup / "private_documents").resolve(strict=True)
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as sqlite:
        sqlite.row_factory = sqlite3.Row
        if sqlite.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite backup failed its integrity check.")
        tables = sqlite.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT GLOB 'sqlite_*' ORDER BY name"
        ).fetchall()

        available = {path.resolve() for path in uploads.rglob("*") if path.is_file()}
        referenced = {
            (uploads / row[0]).resolve()
            for row in sqlite.execute("SELECT stored_filename FROM resume_documents")
        }
        if available != referenced:
            raise ValueError("The backed-up files do not match the document records.")

        with raw_connection(dsn) as pg:
            pg.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(SCHEMA)))
            pg.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(SCHEMA)))
            pg.execute(postgres_schema())
            pg.execute("ALTER TABLE resume_documents ADD COLUMN file_bytes BYTEA NOT NULL")
            for (table,) in tables:
                target = sql.Identifier(table)
                quoted = '"' + table.replace('"', '""') + '"'
                rows = sqlite.execute(f"SELECT * FROM {quoted}")
                columns = [column[0] for column in rows.description]
                if table == "resume_documents":
                    columns.append("file_bytes")
                insert = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    target,
                    sql.SQL(", ").join(map(sql.Identifier, columns)),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                )
                count = 0
                for row in rows:
                    values = list(row)
                    if table == "resume_documents":
                        path = (uploads / row["stored_filename"]).resolve(strict=True)
                        if not path.is_relative_to(uploads):
                            raise ValueError("Invalid stored document path.")
                        data = path.read_bytes()
                        if row["file_hash"] and sha256(data).hexdigest() != row["file_hash"]:
                            raise ValueError("A backed-up document failed its hash check.")
                        values[columns.index("storage_path")] = path.name
                        values.append(data)
                    pg.execute(insert, values)
                    count += 1
                actual = pg.execute(sql.SQL("SELECT count(*) FROM {}").format(target)).fetchone()[0]
                if actual != count:
                    raise RuntimeError(f"Imported row count differs for {table}.")
                if "id" in columns:
                    sequence = pg.execute(
                        "SELECT pg_get_serial_sequence(%s, 'id')", (f"{SCHEMA}.{table}",)
                    ).fetchone()[0]
                    if sequence and count:
                        last = pg.execute(sql.SQL("SELECT max(id) FROM {}").format(target)).fetchone()[0]
                        pg.execute("SELECT setval(%s::regclass, %s)", (sequence, last))
            for filename, file_data in pg.execute(
                "SELECT stored_filename, file_bytes FROM resume_documents"
            ):
                if bytes(file_data) != (uploads / filename).read_bytes():
                    raise RuntimeError("An imported document differs from its backup.")
            print("Database rows and document bytes verified.")
    print("Migration committed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    args = parser.parse_args()
    migrate(args.backup, os.environ["DATABASE_URL"])
