"""
Database initialization and utility functions for Bakery Management System
"""
import pyodbc
import datetime
from werkzeug.security import generate_password_hash
from flask import current_app as app

def get_db_connection():
    """
    Establish a connection to the database.
    Tries Windows Authentication first, then falls back to SQL Server Authentication.
    """
    try:
        # Try Windows Authentication first with master database
        conn_str = (f'DRIVER={app.config["SQL_SERVER_DRIVER"]};'
                  f'SERVER={app.config["SQL_SERVER"]};'
                  f'DATABASE=master;'
                  f'Trusted_Connection=yes;')
        conn = pyodbc.connect(conn_str)
        
        # Create the BMS database if it doesn't exist
        cursor = conn.cursor()
        cursor.execute("IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BMS') CREATE DATABASE BMS")
        conn.commit()
        conn.close()
        
        # Now connect to the BMS database
        conn_str = (f'DRIVER={app.config["SQL_SERVER_DRIVER"]};'
                  f'SERVER={app.config["SQL_SERVER"]};'
                  f'DATABASE={app.config["DATABASE"]};'
                  f'Trusted_Connection=yes;')
        conn = pyodbc.connect(conn_str)
        return conn
    except:
        try:
            # Try SQL Server Authentication with master database first
            conn_str = (f'DRIVER={app.config["SQL_SERVER_DRIVER"]};'
                      f'SERVER={app.config["SQL_SERVER"]};'
                      f'DATABASE=master;'
                      f'UID={app.config["SQL_USERNAME"]};'
                      f'PWD={app.config["SQL_PASSWORD"]};')
            conn = pyodbc.connect(conn_str)
            
            # Create the BMS database if it doesn't exist
            cursor = conn.cursor()
            cursor.execute("IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BMS') CREATE DATABASE BMS")
            conn.commit()
            conn.close()
            
            # Now connect to the BMS database
            conn_str = (f'DRIVER={app.config["SQL_SERVER_DRIVER"]};'
                      f'SERVER={app.config["SQL_SERVER"]};'
                      f'DATABASE={app.config["DATABASE"]};'
                      f'UID={app.config["SQL_USERNAME"]};'
                      f'PWD={app.config["SQL_PASSWORD"]};')
            conn = pyodbc.connect(conn_str)
            return conn
        except pyodbc.Error as e:
            print(f"Database connection error: {str(e)}")
            raise

def init_db():
    """
    Initialize the database with required tables if they don't exist
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL UNIQUE,
        password NVARCHAR(255) NOT NULL,
        role NVARCHAR(20) NOT NULL
    )
    ''')
    
    # Create products table
    cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'products')
    CREATE TABLE products (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        image NVARCHAR(255)
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'orders')
    CREATE TABLE orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id NVARCHAR(50) NOT NULL UNIQUE,
        customer_name NVARCHAR(100) NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL,
        order_date DATETIME NOT NULL
    )
    ''')
    
    # Create order_items table
    cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'order_items')
    CREATE TABLE order_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id NVARCHAR(50) NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')
    
    # Check if default admin user exists, if not create it
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     ('admin', password_hash, 'admin'))
    
    # Check if default manager user exists, if not create it
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'manager'")
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('manager123')
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     ('manager', password_hash, 'manager'))
    
    conn.commit()
    conn.close()

def generate_order_id():
    """
    Generate a unique order ID based on current timestamp
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # Add some randomness to ensure uniqueness
    import random
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
    return f"{timestamp}{random_suffix}"

def get_all_products():
    """
    Get all products from the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, quantity, price, image FROM products')
    products = cursor.fetchall()
    
    # Convert to list of dictionaries
    products_list = []
    for product in products:
        products_list.append({
            'id': product[0],
            'name': product[1],
            'quantity': product[2],
            'price': product[3],
            'image': product[4]
        })
    
    conn.close()
    return products_list

def get_product_by_id(product_id):
    """
    Get a product by its ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, quantity, price, image FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    if product:
        product_dict = {
            'id': product[0],
            'name': product[1],
            'quantity': product[2],
            'price': product[3],
            'image': product[4]
        }
    else:
        product_dict = None
    
    conn.close()
    return product_dict

def add_product(name, quantity, price, image):
    """
    Add a new product to the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, quantity, price, image) VALUES (?, ?, ?, ?)',
        (name, quantity, price, image)
    )
    conn.commit()
    conn.close()

def update_product(product_id, name, quantity, price, image=None):
    """
    Update an existing product
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if image:
        cursor.execute(
            'UPDATE products SET name = ?, quantity = ?, price = ?, image = ? WHERE id = ?',
            (name, quantity, price, image, product_id)
        )
    else:
        cursor.execute(
            'UPDATE products SET name = ?, quantity = ?, price = ? WHERE id = ?',
            (name, quantity, price, product_id)
        )
    
    conn.commit()
    conn.close()

def delete_product(product_id):
    """
    Delete a product from the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

def create_order(customer_name, order_items):
    """
    Create a new order
    order_items: list of dictionaries with product_id, quantity, price
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate order ID
    order_id = generate_order_id()
    order_date = datetime.datetime.now()
    
    # Calculate total price
    total_price = sum(item['price'] for item in order_items)
    
    # Insert order
    cursor.execute(
        'INSERT INTO orders (order_id, customer_name, total_price, order_date) VALUES (?, ?, ?, ?)',
        (order_id, customer_name, total_price, order_date)
    )
    
    # Insert order items
    for item in order_items:
        cursor.execute(
            'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, item['product_id'], item['quantity'], item['price'])
        )
    
    conn.commit()
    conn.close()
    
    return order_id

def get_order(order_id):
    """
    Get order details by order_id
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get order information
    cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return None, None
    
    # Get order items
    cursor.execute('''
        SELECT oi.*, p.name 
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items = cursor.fetchall()
    
    # Convert to dictionaries
    order_dict = {
        'id': order[0],
        'order_id': order[1],
        'customer_name': order[2],
        'total_amount': order[3],
        'order_date': order[4]
    }
    
    items_list = []
    for item in items:
        items_list.append({
            'id': item[0],
            'order_id': item[1],
            'product_id': item[2],
            'quantity': item[3],
            'price': item[4],
            'product_name': item[5]  # From the JOIN with products table
        })
    
    conn.close()
    return order_dict, items_list

def get_all_orders():
    """
    Get all orders from the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all orders with customer name and date
    cursor.execute('''
        SELECT id, order_id, customer_name, order_date, total_price 
        FROM orders 
        ORDER BY order_date DESC
    ''')
    orders = cursor.fetchall()
    
    # Convert to list of dictionaries
    orders_list = []
    for order in orders:
        orders_list.append({
            'id': order[0],
            'order_id': order[1],
            'customer_name': order[2],
            'order_date': order[3],
            'total_amount': order[4]
        })
        
    conn.close()
    return orders_list

def verify_user(username, password):
    """
    Verify user credentials
    Returns None if user not found or password incorrect
    Returns user data if authenticated
    """
    from werkzeug.security import check_password_hash
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[2], password):
        return user
    
    return None
