SAZON & SON Restaurant Ordering System
A Django-based restaurant ordering system designed to run on Raspberry Pi with smartphone interface.

Features
📱 Mobile-first responsive design
🍽️ Complete menu management system
📝 Order creation and management
🖨️ Kitchen printer integration
📊 Real-time order tracking
🔄 RESTful API
Requirements
Python 3.9+
Django 4.2+
Raspberry Pi (for production)
CUPS (for printing)
Installation
1. Clone the repository:
bash
git clone https://github.com/yourusername/restaurant-system.git
cd restaurant-system
2. Create and activate virtual environment:
On macOS/Linux:

bash
python3 -m venv venv
source venv/bin/activate
On Windows:

bash
python -m venv venv
venv\Scripts\activate
3. Install required packages:
bash
pip install --upgrade pip
pip install django==4.2.7
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.0
pip install Pillow==10.1.0
pip install python-decouple==3.8
pip install reportlab==4.0.7

# Optional: For printing support
pip install pycups==2.0.1  # For CUPS printing (Linux/Mac)
# pip install python-escpos==3.0  # For thermal printers (optional)
Or install all at once:

bash
pip install -r requirements.txt
4. Create Django project structure:
bash
# If starting fresh (skip if cloned from repo)
django-admin startproject restaurant_system .

# Create necessary apps
python manage.py startapp menu
python manage.py startapp orders
python manage.py startapp api
5. Configure environment variables:
bash
# Create .env file from example
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
Required .env variables:

bash
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
6. Update Django settings:
Add apps to INSTALLED_APPS in restaurant_system/settings.py:

python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'corsheaders',
    # Local apps
    'menu',
    'orders',
    'api',
]
Add CORS middleware:

python
MIDDLEWARE = [
    # ... other middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]
7. Create and run database migrations:
bash
# Create migration files
python manage.py makemigrations menu
python manage.py makemigrations orders

# Apply migrations to database
python manage.py migrate

# Check migration status
python manage.py showmigrations
8. Create management commands directories:
bash
# Create management command structure for menu app
mkdir -p menu/management/commands
touch menu/management/__init__.py
touch menu/management/commands/__init__.py

# Copy the load_menu.py and reset_menu.py files to:
# menu/management/commands/load_menu.py
# menu/management/commands/reset_menu.py
9. Load initial menu data:
bash
# Load the menu items from the management command
python manage.py load_menu

# Optional: Reset and reload menu data
# python manage.py reset_menu --clear-orders
10. Create superuser for admin access:
bash
python manage.py createsuperuser
# Follow prompts:
# Username: admin
# Email: admin@sazonyson.com
# Password: [your-secure-password]
11. Collect static files (for production):
bash
# Create static directories
mkdir -p static
mkdir -p media

# Collect static files
python manage.py collectstatic --noinput
12. Create templates directory and add HTML file:
bash
# Create templates directory
mkdir -p templates

# Copy order.html to templates/order.html
# Make sure to add templates directory to settings.py:
# TEMPLATES = [
#     {
#         ...
#         'DIRS': [BASE_DIR / 'templates'],
#         ...
#     }
# ]
13. Run development server:
bash
# Run on all interfaces (accessible from network)
python manage.py runserver 0.0.0.0:8000

# Or just locally
python manage.py runserver
14. Access the application:
Home/Order Page: http://localhost:8000/
Admin Panel: http://localhost:8000/admin/
API Root: http://localhost:8000/api/
Categories API: http://localhost:8000/api/categories/
Menu Items API: http://localhost:8000/api/menu-items/
Orders API: http://localhost:8000/api/orders/
Testing the API
Test with curl commands:
bash
# Get all categories
curl http://localhost:8000/api/categories/

# Get all menu items
curl http://localhost:8000/api/menu-items/

# Create a test order
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": "5",
    "customer_name": "Test Customer",
    "items": [
      {"menu_item_id": 1, "quantity": 2},
      {"menu_item_id": 2, "quantity": 1}
    ]
  }'
Raspberry Pi Deployment
Additional steps for Raspberry Pi:
Update Raspberry Pi:
bash
sudo apt update
sudo apt upgrade -y
Install Python and dependencies:
bash
sudo apt install python3-pip python3-venv python3-dev
sudo apt install nginx
sudo apt install cups  # For printing support
Install and configure Gunicorn:
bash
pip install gunicorn

# Test Gunicorn
gunicorn --bind 0.0.0.0:8000 restaurant_system.wsgi

# Create systemd service file
sudo nano /etc/systemd/system/gunicorn.service
Configure CUPS for printing (optional):
bash
# Add user to lpadmin group
sudo usermod -a -G lpadmin pi

# Access CUPS admin
# http://raspberry-pi-ip:631
Set up as system service:
bash
# Enable and start service
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Check status
sudo systemctl status gunicorn
Configure Nginx:
bash
sudo nano /etc/nginx/sites-available/restaurant_system
sudo ln -s /etc/nginx/sites-available/restaurant_system /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
Troubleshooting
Common Issues and Solutions:
Database errors:
bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py load_menu
Permission errors:
bash
# Fix permissions
chmod +x manage.py
chmod -R 755 media/
chmod -R 755 static/
Module not found errors:
bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall requirements
pip install -r requirements.txt
Port already in use:
bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
python manage.py runserver 0.0.0.0:8001
Static files not loading:
bash
# Check STATIC_URL and STATIC_ROOT in settings.py
python manage.py collectstatic --noinput
Development Workflow
Making changes to menu items:
bash
# Modify menu/models.py
# Then run:
python manage.py makemigrations
python manage.py migrate
python manage.py reset_menu  # To reload menu data
Testing orders:
bash
# Django shell
python manage.py shell

>>> from orders.models import Order
>>> Order.objects.all()
>>> Order.objects.filter(status='pending')
Checking logs:
bash
# Development
python manage.py runserver --verbosity 2

# Production (with systemd)
sudo journalctl -u gunicorn -f
Support
For issues or questions:

Check the logs: logs/ directory
Admin panel: http://localhost:8000/admin/
API documentation: http://localhost:8000/api/
License
This project is proprietary software for SAZON & SON Cocina-Bar.