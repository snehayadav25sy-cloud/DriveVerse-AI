import sqlite3

DB_PATH = r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\database\gwm.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get existing columns in datasets table
cur.execute("PRAGMA table_info(datasets)")
existing_cols = [row[1] for row in cur.fetchall()]
print(f"Existing columns in datasets: {existing_cols}")

cols_to_add = [
    ("rgb_count", "INTEGER DEFAULT 0"),
    ("lidar_count", "INTEGER DEFAULT 0"),
    ("annotation_count", "INTEGER DEFAULT 0"),
]

for col_name, col_type in cols_to_add:
    if col_name not in existing_cols:
        alter_sql = f"ALTER TABLE datasets ADD COLUMN {col_name} {col_type}"
        print(f"Executing: {alter_sql}")
        cur.execute(alter_sql)
        print(f"Added column: {col_name}")

conn.commit()
conn.close()
print("Database schema migration complete!")
