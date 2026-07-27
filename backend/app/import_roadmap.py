import argparse

from app.db import get_connection, init_db, upsert_roadmap
from app.roadmap_parser import list_available_roadmaps, parse_roadmap


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa um roadmap do developer-roadmap para o SQLite local")
    parser.add_argument("slug", nargs="?", help="Slug do roadmap (ex: backend). Se omitido, lista os disponiveis.")
    args = parser.parse_args()

    if not args.slug:
        for slug in list_available_roadmaps():
            print(slug)
        return

    parsed = parse_roadmap(args.slug)
    conn = get_connection()
    init_db(conn)
    upsert_roadmap(conn, parsed["nodes"], parsed["edges"])
    conn.close()
    print(f"Importado '{args.slug}': {len(parsed['nodes'])} nos, {len(parsed['edges'])} arestas")


if __name__ == "__main__":
    main()
