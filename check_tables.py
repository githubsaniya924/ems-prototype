import sqlite3

conn = sqlite3.connect("incidents.db")
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables:")
for table in tables:
    print(f"- {table[0]}")

print("\nSchema Details:\n")
for table in tables:
    table_name = table[0]
    if table_name != 'sqlite_sequence':
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"{table_name}:")
        for col in columns:
            # col = (cid, name, type, notnull, dflt_value, pk)
            print(f"  - {col[1]} ({col[2]})")
        print()

conn.close()
