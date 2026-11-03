# Inventory Management System

A Flask + MySQL web application for managing products, suppliers, purchases, sales and stock.

## Requirements
- Python 3.10 or newer
- MySQL Server 8.x
- A web browser

## Setup

1. Install Python and MySQL.
2. Open MySQL Workbench or MySQL command line.
3. Run the complete `schema.sql` file. This creates `inventory_db` and its three tables.
4. Open `app.py` and change `YOUR_MYSQL_PASSWORD` to your MySQL root password. If your MySQL user has no password, use an empty string.
5. Open a terminal in this project folder and run:

   ```bash
   python -m venv venv
   ```

   Windows:
   ```bash
   venv\Scripts\activate
   ```

   macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

6. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

7. Start the application:

   ```bash
   python app.py
   ```

8. Open `http://127.0.0.1:5000` in your browser.

## Features
- Dashboard with product, supplier and stock counts
- Add, edit, delete and search products
- Add, edit and delete suppliers
- Record purchases (increases stock)
- Record sales (decreases stock)
- Blocks sales when stock is insufficient
- Low-stock report
- Transaction history

## Important notes
- A supplier is required for a purchase; sales are not linked to a supplier.
- Existing transaction history is protected by foreign keys, so linked products or suppliers cannot be deleted.
- Change the Flask secret key and database credentials before deployment.
- This is an educational mini-project. Add login/roles, CSRF protection, production configuration and backups before real business use.
