from app.db.sqlite_client import get_sqlite_conn

with get_sqlite_conn() as conn:
    cur = conn.cursor()

    print("\n===== CONNECTIONS =====")
    cur.execute("SELECT * FROM connections LIMIT 10")
    for row in cur.fetchall():
        print(dict(row))

    print("\n===== INTERCHANGES =====")
    cur.execute("SELECT * FROM interchanges LIMIT 10")
    for row in cur.fetchall():
        print(dict(row))