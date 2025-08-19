# seed_sqlite.py
import sqlalchemy as sa

engine = sa.create_engine("sqlite:///demo.db")
with engine.begin() as c:
    c.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS customers(
          customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT, email TEXT, region TEXT
        );""")
    c.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS orders(
          order_id INTEGER PRIMARY KEY AUTOINCREMENT,
          customer_id INTEGER, order_date DATE, status TEXT
        );""")
    c.exec_driver_sql("""  
        CREATE TABLE IF NOT EXISTS order_items(
          order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_id INTEGER, product TEXT, quantity INTEGER, unit_price REAL
        );""")
    # seed minimal data once
    n = c.exec_driver_sql("SELECT COUNT(*) FROM customers").scalar()
    if n == 0:
        c.exec_driver_sql("""
          INSERT INTO customers(name,email,region) VALUES
          ('Alice Smith','alice@example.com','EMEA'),
          ('Bob Jones','bob@example.com','AMER'),
          ('Chen Li','chen@example.com','APAC');
        """)
        c.exec_driver_sql("""
          INSERT INTO orders(customer_id,order_date,status) VALUES
          (1,'2025-07-28','shipped'),
          (2,'2025-07-30','processing'),
          (3,'2025-08-02','shipped');
        """)
        c.exec_driver_sql("""
          INSERT INTO order_items(order_id,product,quantity,unit_price) VALUES
          (1,'Gadget',2,199.99),
          (1,'Cable',3,19.90),
          (2,'Widget',1,99.50),
          (3,'Widget',4,99.50);
        """)
print("Seeded demo.db")
