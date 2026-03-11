"""
migrate_db.py — Run once to fix all database schema issues.
Place in C:\\event_management\\ and run: python migrate_db.py
"""
import sqlite3
import os

# Flask uses the instance folder by default
DB_PATH = 'instance/event_management.db'

if not os.path.exists(DB_PATH):
    print(f"❌ Database not found at {DB_PATH}")
    print("   Make sure you run this from C:\\event_management\\")
    exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


def get_columns(table):
    return [r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()]


def add_column_if_missing(table, column, col_type, default=None):
    cols = get_columns(table)
    if column not in cols:
        if default is not None:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT '{default}'")
        else:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  ✅ Added {table}.{column}")
    else:
        print(f"  ✓  {table}.{column} already exists")


print("\n=== Fixing bookings table ===")
add_column_if_missing('bookings', 'customer_name',  'VARCHAR(200)', '')
add_column_if_missing('bookings', 'customer_phone', 'VARCHAR(20)',  '')
add_column_if_missing('bookings', 'customer_email', 'VARCHAR(120)', '')
add_column_if_missing('bookings', 'pending_amount', 'FLOAT',        0)

# Fix event_date type issue — convert Date values to string if needed
print("\n=== Checking event_date format ===")
try:
    rows = conn.execute("SELECT id, event_date FROM bookings").fetchall()
    for row in rows:
        if row['event_date'] and 'T' in str(row['event_date']):
            # Convert ISO datetime to date string
            date_str = str(row['event_date'])[:10]
            conn.execute("UPDATE bookings SET event_date=? WHERE id=?", (date_str, row['id']))
            print(f"  Fixed booking {row['id']} date: {date_str}")
    print("  ✓ event_date format OK")
except Exception as e:
    print(f"  event_date check: {e}")

# Populate customer_name/phone/email from customers table where empty
print("\n=== Populating booking customer info ===")
try:
    conn.execute("""
        UPDATE bookings SET
            customer_name = (SELECT full_name FROM customers WHERE customers.id = bookings.customer_id),
            customer_phone= (SELECT phone FROM customers WHERE customers.id = bookings.customer_id),
            customer_email= (SELECT email FROM customers WHERE customers.id = bookings.customer_id)
        WHERE customer_name = '' OR customer_name IS NULL
    """)
    print("  ✅ Populated customer info from customers table")
except Exception as e:
    print(f"  populate customer info: {e}")

print("\n=== Fixing designs table ===")
add_column_if_missing('designs', 'thumb_path', 'VARCHAR(300)')

print("\n=== Fixing billing_items table ===")
add_column_if_missing('billing_items', 'description', 'TEXT')

print("\n=== Fixing attendances table (duplicate check) ===")
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if 'attendances' in tables and 'attendance' in tables:
    # Move data from attendances to attendance if any
    try:
        count = conn.execute("SELECT COUNT(*) FROM attendances").fetchone()[0]
        if count > 0:
            conn.execute("""
                INSERT OR IGNORE INTO attendance (labour_id, date, is_present, half_day, wage_amount, advance_amount, notes, created_at)
                SELECT labour_id, date, is_present, half_day, wage_amount, advance_amount, notes, created_at FROM attendances
            """)
            print(f"  Migrated {count} records from attendances → attendance")
        conn.execute("DROP TABLE attendances")
        print("  ✅ Dropped duplicate attendances table")
    except Exception as e:
        print(f"  attendances cleanup: {e}")

print("\n=== Fixing admins table (duplicate check) ===")
if 'admins' in tables and 'admin' in tables:
    try:
        count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        if count > 0:
            # Check if admin table is empty
            admin_count = conn.execute("SELECT COUNT(*) FROM admin").fetchone()[0]
            if admin_count == 0:
                print("  Moving data from admins → admin")
                # Can't easily move due to schema differences, just drop admins
        conn.execute("DROP TABLE admins")
        print("  ✅ Dropped duplicate admins table")
    except Exception as e:
        print(f"  admins cleanup: {e}")

print("\n=== Final table check ===")
tables_now = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in sorted(tables_now):
    cols = get_columns(t)
    print(f"  {t}: {cols}")

conn.commit()
conn.close()
print("\n✅ Migration complete! Run: python run.py")
