from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pyodbc  # Change to pyodbc for SQL Server
import os
import datetime
import uuid
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from functools import wraps

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Create DB connection for SQL Server
def get_db_connection():
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

# Initialize the database
def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users table exists, if not create it
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
        BEGIN
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(100) NOT NULL UNIQUE,
                password NVARCHAR(255) NOT NULL,
                role NVARCHAR(50) NOT NULL
            )
        END
        """)
        
        # Check if products table exists, if not create it
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'products')
        BEGIN
            CREATE TABLE products (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                quantity NVARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                image NVARCHAR(255)
            )
        END
        """)
        
        # Check if orders table exists, if not create it
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'orders')
        BEGIN
            CREATE TABLE orders (
                id INT IDENTITY(1,1) PRIMARY KEY,
                order_id NVARCHAR(50) NOT NULL UNIQUE,
                customer_name NVARCHAR(255) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                order_date DATETIME NOT NULL
            )
        END
        """)
        
        # Check if order_items table exists, if not create it
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'order_items')
        BEGIN
            CREATE TABLE order_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                order_id NVARCHAR(50) NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                CONSTRAINT fk_order_items_products FOREIGN KEY (product_id) REFERENCES products(id),
                CONSTRAINT fk_order_items_orders FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        END
        """)
        
        # Check if default admin user exists, if not create it
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = generate_password_hash('admin123')
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                         ('admin', password_hash, 'admin'))
        
        conn.commit()
        conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('Admin privileges required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):  # Indexing fields since we're using pyodbc
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_role'] = user[3]
            
            if user[3] == 'admin':  # Accessing role field at index 3
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('place_order'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/products')
@login_required
@admin_required
def product_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    
    # Convert the pyodbc result to a list of dictionaries for easier template access
    product_list = []
    for product in products:
        product_list.append({
            'id': product[0],
            'name': product[1],
            'quantity': product[2],
            'price': product[3],
            'image': product[4]
        })
    
    return render_template('admin/product_list.html', products=product_list)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        image_filename = None
        
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                image_filename = f"{uuid.uuid4()}_{filename}"
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, quantity, price, image) VALUES (?, ?, ?, ?)',
                     (name, quantity, price, image_filename))
        conn.commit()
        conn.close()
        
        flash('Product added successfully', 'success')
        return redirect(url_for('product_list'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product_data = cursor.fetchone()
    
    if not product_data:
        conn.close()
        flash('Product not found', 'error')
        return redirect(url_for('product_list'))
    
    # Convert to dictionary for easier template access
    product = {
        'id': product_data[0],
        'name': product_data[1],
        'quantity': product_data[2],
        'price': product_data[3],
        'image': product_data[4]
    }
    
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        image_filename = product['image']
        
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                # Delete old image if it exists
                if image_filename:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    except:
                        pass
                
                filename = secure_filename(image.filename)
                image_filename = f"{uuid.uuid4()}_{filename}"
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        cursor.execute('UPDATE products SET name = ?, quantity = ?, price = ?, image = ? WHERE id = ?',
                     (name, quantity, price, image_filename, id))
        conn.commit()
        conn.close()
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('product_list'))
    
    conn.close()
    return render_template('admin/add_product.html', product=product, edit=True)

@app.route('/admin/orders-history')
@login_required
@admin_required
def orders_history():
    try:
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
        return render_template('admin/orders_history.html', orders=orders_list)
    except Exception as e:
        print(f"Error fetching orders history: {str(e)}")
        flash('An error occurred while loading orders history', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/orders/<order_id>')
@login_required
@admin_required
def view_order_details(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get order information
        cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('orders_history'))
        
        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name 
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()
        
        conn.close()
        
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
                'product_name': item[5]
            })
        
        return render_template('admin/order_details.html', order=order_dict, items=items_list)
    except Exception as e:
        print(f"Error viewing order details: {str(e)}")
        flash(f"Error viewing order details: {str(e)}", 'error')
        return redirect(url_for('orders_history'))

@app.route('/manager')
def manager_redirect():
    return redirect(url_for('place_order'))

def generate_order_id():
    # Generates a unique order ID using UUID
    return str(uuid.uuid4())

@app.route('/manager/place-order', methods=['GET', 'POST'])
@login_required
def place_order():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all available products
    cursor.execute('SELECT id, name, quantity, price, image FROM products')
    products_data = cursor.fetchall()
    
    # Convert to list of dictionaries for easier template access
    products = []
    for product in products_data:
        products.append({
            'id': product[0],
            'name': product[1],
            'quantity': product[2],
            'price': product[3],
            'image': product[4]
        })
    
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        product_ids = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')
        
        if not product_ids or not quantities or len(product_ids) != len(quantities):
            flash('Please select at least one product with a valid quantity', 'error')
            return render_template('manager/place_order.html', products=products)
        
        # Generate a unique order ID
        order_id = generate_order_id()
        order_date = datetime.datetime.now()
        total_price = 0
        
        # Calculate total price and prepare order items
        order_items = []
        for i in range(len(product_ids)):
            if int(quantities[i]) <= 0:
                continue
                
            # Get product price
            cursor.execute('SELECT price FROM products WHERE id = ?', (product_ids[i],))
            product_price = cursor.fetchone()[0]
            item_total = float(product_price) * int(quantities[i])
            total_price += item_total
            
            order_items.append({
                'product_id': product_ids[i],
                'quantity': quantities[i],
                'price': item_total
            })
        
        if not order_items:
            flash('Please select at least one product with a valid quantity', 'error')
            return render_template('manager/place_order.html', products=products)
        
        try:
            # Insert the order
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
            
            # Redirect to invoice page
            return redirect(url_for('invoice', order_id=order_id))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error creating order: {str(e)}', 'error')
            return render_template('manager/place_order.html', products=products)
    
    conn.close()
    return render_template('manager/place_order.html', products=products)

@app.route('/manager/invoice/<order_id>')
@login_required
def invoice(order_id):
    try:
        # Get order details from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get order information
        cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('place_order'))
        
        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name 
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        # Convert to dictionaries for easier template access
        # Fixing the order of fields based on your database schema
        order_dict = {
            'id': order[0],
            'order_id': order[1],
            'customer_name': order[2],
            'total_amount': order[3],  # This is total_price in the database
            'order_date': order[4]     # This is order_date in the database
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
        
        return render_template('manager/invoice.html', order=order_dict, items=items_list)
    except Exception as e:
        print(f"Error in invoice route: {str(e)}")
        flash(f"Error generating invoice: {str(e)}", 'error')
        return redirect(url_for('place_order'))

@app.route('/manager/download-invoice/<order_id>')
def download_invoice(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order_data = cursor.fetchone()
    
    if not order_data:
        conn.close()
        flash('Order not found', 'error')
        return redirect(url_for('place_order'))
    
    # Convert order to dictionary
    order = {
        'id': order_data[0],
        'order_id': order_data[1],
        'customer_name': order_data[2],
        'total_price': order_data[3],
        'order_date': order_data[4]
    }
    
    cursor.execute('''
        SELECT oi.*, p.name as product_name, p.price as unit_price
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items_data = cursor.fetchall()
    
    items = []
    for item in items_data:
        items.append({
            'product_name': item[5],
            'quantity': item[3],
            'unit_price': item[6],
            'price': item[4]
        })
    
    conn.close()
    
    # Create a PDF invoice
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "Bakery Management System")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, f"Invoice #{order['order_id']}")
    p.drawString(50, 710, f"Date: {order['order_date']}")
    p.drawString(50, 690, f"Customer: {order['customer_name']}")
    
    p.line(50, 680, 550, 680)
    p.drawString(50, 660, "Product")
    p.drawString(250, 660, "Quantity")
    p.drawString(350, 660, "Unit Price")
    p.drawString(450, 660, "Total")
    p.line(50, 650, 550, 650)
    
    y = 630
    for item in items:
        p.drawString(50, y, item['product_name'])
        p.drawString(250, y, str(item['quantity']))
        p.drawString(350, y, f"${item['unit_price']:.2f}")
        p.drawString(450, y, f"${item['price']:.2f}")
        y -= 20
    
    p.line(50, y, 550, y)
    p.drawString(350, y - 20, "Total:")
    p.drawString(450, y - 20, f"${order['total_price']:.2f}")
    
    p.drawString(50, 100, "Thank you for your business!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"invoice_{order['order_id']}.pdf"
    )

@app.route('/api/get-products')
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price FROM products')
    products_data = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': product[0],
        'name': product[1],
        'price': product[2]
    } for product in products_data])

if __name__ == '__main__':
    # Check if the upload folder exists, create it if it doesn't
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Initialize the database
    init_db()
    
    app.run(debug=True)