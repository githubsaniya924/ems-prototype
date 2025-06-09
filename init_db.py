import sqlite3

conn = sqlite3.connect("incidents.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    location TEXT,
    photo_path TEXT,
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


c.execute('''
    CREATE TABLE IF NOT EXISTS usersDetails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

# Create the admin_users table
c.execute('''
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Insert new admin user (you can include email if you added it)
c.execute('''
    INSERT INTO admin_users (username, password)
    VALUES (?, ?)
''', ('abc', 'abc@123'))

c.execute('''
    INSERT INTO admin_users (username, password)
    VALUES (?, ?)
''', ('xyz', 'xyz@123'))


c.execute("""
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL,   -- 'flood', 'sewer', 'water'
    area TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

c.execute(""" 
        ALTER TABLE incidents ADD COLUMN status TEXT DEFAULT 'Open'; """)

c.execute("UPDATE incidents SET status = 'Pending' WHERE status = 'Open'")
c.execute("UPDATE incidents SET status = 'Done' WHERE status = 'Closed'")



conn.commit()
conn.close()

print("Database initialized with 'incidents' table.")
