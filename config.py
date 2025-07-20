import os

# Secret key for session management
SECRET_KEY = 'your-secret-key-for-bakery-app'

# SQL Server connection settings
SQL_SERVER = 'DESKTOP-67QUF6V\\SQLEXPRESS'  # Use double backslash to escape
SQL_SERVER_DRIVER = '{ODBC Driver 17 for SQL Server}'  # Use the actual ODBC driver name
DATABASE = 'BMS'  # Your existing database name
SQL_USERNAME = 'sa'  # SQL Server authentication username
SQL_PASSWORD = '123456'  # Replace with your actual SQL Server password
TRUSTED_CONNECTION = 'yes'  # Try using Windows authentication instead

# File upload settings
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit