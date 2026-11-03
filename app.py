import os
from dotenv import load_dotenv

load_dotenv()
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "inventory_db")
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.template_filter("inr")
def inr(value):
    return f"₹{Decimal(str(value or 0)):,.2f}"

@app.route("/")
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM products")
    total_products = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM suppliers")
    total_suppliers = cur.fetchone()["total"]
    cur.execute("SELECT COALESCE(SUM(quantity),0) AS total FROM products")
    total_units = cur.fetchone()["total"]
    cur.execute("""
        SELECT product_id, product_name, quantity, reorder_level
        FROM products WHERE quantity <= reorder_level
        ORDER BY quantity ASC LIMIT 8
    """)
    low_stock = cur.fetchall()
    cur.execute("""
        SELECT t.transaction_id, p.product_name, s.name AS supplier_name,
               t.transaction_type, t.quantity, t.transaction_date
        FROM stock_transactions t
        JOIN products p ON p.product_id=t.product_id
        LEFT JOIN suppliers s ON s.supplier_id=t.supplier_id
        ORDER BY t.transaction_id DESC LIMIT 8
    """)
    recent = cur.fetchall()
    cur.close(); conn.close()
    return render_template("dashboard.html", total_products=total_products,
        total_suppliers=total_suppliers, total_units=total_units,
        low_stock=low_stock, recent=recent)

@app.route("/products")
def products():
    search = request.args.get("q", "").strip()
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM products
        WHERE product_name LIKE %s OR category LIKE %s
        ORDER BY product_id DESC
    """, (f"%{search}%", f"%{search}%"))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("products.html", products=rows, search=search)

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = Decimal(request.form.get("price", ""))
            quantity = int(request.form.get("quantity", ""))
            reorder = int(request.form.get("reorder_level", ""))
            if not name or price < 0 or quantity < 0 or reorder < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            flash("Enter valid product details. Values cannot be negative.", "danger")
            return render_template("product_form.html", product=None)
        conn = get_db(); cur = conn.cursor()
        cur.execute("""INSERT INTO products
            (product_name, category, price, quantity, reorder_level)
            VALUES (%s,%s,%s,%s,%s)""",
            (name, category, price, quantity, reorder))
        conn.commit(); cur.close(); conn.close()
        flash("Product added successfully.", "success")
        return redirect(url_for("products"))
    return render_template("product_form.html", product=None)

@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE product_id=%s", (product_id,))
    product = cur.fetchone()
    if not product:
        cur.close(); conn.close()
        flash("Product not found.", "danger")
        return redirect(url_for("products"))
    if request.method == "POST":
        name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = Decimal(request.form.get("price", ""))
            reorder = int(request.form.get("reorder_level", ""))
            if not name or price < 0 or reorder < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            flash("Enter valid details. Price and reorder level cannot be negative.", "danger")
            cur.close(); conn.close()
            return render_template("product_form.html", product=product)
        cur.execute("""UPDATE products SET product_name=%s, category=%s,
            price=%s, reorder_level=%s WHERE product_id=%s""",
            (name, category, price, reorder, product_id))
        conn.commit(); cur.close(); conn.close()
        flash("Product updated successfully.", "success")
        return redirect(url_for("products"))
    cur.close(); conn.close()
    return render_template("product_form.html", product=product)

@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE product_id=%s", (product_id,))
        conn.commit()
        flash("Product deleted.", "success")
    except Error:
        conn.rollback()
        flash("Cannot delete this product because it has stock transaction history.", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("products"))

@app.route("/suppliers")
def suppliers():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("suppliers.html", suppliers=rows)

@app.route("/suppliers/add", methods=["GET", "POST"])
def add_supplier():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        company = request.form.get("company", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        if not name:
            flash("Supplier name is required.", "danger")
            return render_template("supplier_form.html")
        conn = get_db(); cur = conn.cursor()
        cur.execute("""INSERT INTO suppliers(name,company,phone,email,address)
            VALUES(%s,%s,%s,%s,%s)""", (name,company,phone,email,address))
        conn.commit(); cur.close(); conn.close()
        flash("Supplier added successfully.", "success")
        return redirect(url_for("suppliers"))
    return render_template("supplier_form.html")

@app.route("/suppliers/edit/<int:supplier_id>", methods=["GET", "POST"])
def edit_supplier(supplier_id):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM suppliers WHERE supplier_id=%s", (supplier_id,))
    supplier = cur.fetchone()
    if not supplier:
        cur.close(); conn.close()
        flash("Supplier not found.", "danger")
        return redirect(url_for("suppliers"))
    if request.method == "POST":
        values = [request.form.get(k, "").strip() for k in
                  ("name","company","phone","email","address")]
        if not values[0]:
            flash("Supplier name is required.", "danger")
            cur.close(); conn.close()
            return render_template("supplier_form.html", supplier=supplier)
        cur.execute("""UPDATE suppliers SET name=%s, company=%s, phone=%s,
            email=%s, address=%s WHERE supplier_id=%s""", (*values,supplier_id))
        conn.commit(); cur.close(); conn.close()
        flash("Supplier updated successfully.", "success")
        return redirect(url_for("suppliers"))
    cur.close(); conn.close()
    return render_template("supplier_form.html", supplier=supplier)

@app.route("/suppliers/delete/<int:supplier_id>", methods=["POST"])
def delete_supplier(supplier_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM suppliers WHERE supplier_id=%s", (supplier_id,))
        conn.commit()
        flash("Supplier deleted.", "success")
    except Error:
        conn.rollback()
        flash("This supplier is linked to transaction history and cannot be deleted.", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("suppliers"))

@app.route("/transactions")
def transactions():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT t.*, p.product_name, s.name AS supplier_name
        FROM stock_transactions t
        JOIN products p ON p.product_id=t.product_id
        LEFT JOIN suppliers s ON s.supplier_id=t.supplier_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("transactions.html", transactions=rows)

@app.route("/stock", methods=["GET", "POST"])
def stock_update():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        try:
            product_id = int(request.form.get("product_id", ""))
            quantity = int(request.form.get("quantity", ""))
            transaction_type = request.form.get("transaction_type", "").upper()
            supplier_raw = request.form.get("supplier_id", "").strip()
            supplier_id = int(supplier_raw) if supplier_raw else None
            if quantity <= 0 or transaction_type not in ("PURCHASE", "SALE"):
                raise ValueError
            if transaction_type == "PURCHASE" and not supplier_id:
                raise ValueError
        except ValueError:
            flash("Choose a valid product, transaction type and positive quantity. Supplier is required for purchases.", "danger")
            cur.execute("SELECT product_id, product_name, quantity FROM products ORDER BY product_name")
            products_list = cur.fetchall()
            cur.execute("SELECT * FROM suppliers ORDER BY name")
            suppliers_list = cur.fetchall()
            cur.close(); conn.close()
            return render_template("stock.html", products=products_list, suppliers=suppliers_list)

        try:
            conn.start_transaction()
            lock_cur = conn.cursor(dictionary=True)
            lock_cur.execute("SELECT quantity FROM products WHERE product_id=%s FOR UPDATE", (product_id,))
            item = lock_cur.fetchone()
            if not item:
                raise ValueError("Product not found.")
            current = item["quantity"]
            if transaction_type == "SALE" and quantity > current:
                raise ValueError(f"Insufficient stock. Available quantity: {current}.")
            new_quantity = current + quantity if transaction_type == "PURCHASE" else current - quantity
            lock_cur.execute("UPDATE products SET quantity=%s WHERE product_id=%s", (new_quantity, product_id))
            lock_cur.execute("""INSERT INTO stock_transactions
                (product_id,supplier_id,transaction_type,quantity,transaction_date)
                VALUES(%s,%s,%s,%s,CURDATE())""",
                (product_id, supplier_id if transaction_type == "PURCHASE" else None,
                 transaction_type, quantity))
            conn.commit()
            flash(f"{transaction_type.title()} recorded. New stock: {new_quantity}.", "success")
            lock_cur.close()
            cur.close(); conn.close()
            return redirect(url_for("transactions"))
        except (Error, ValueError) as exc:
            conn.rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "Database error. Transaction was not saved.", "danger")

    cur.execute("SELECT product_id, product_name, quantity FROM products ORDER BY product_name")
    products_list = cur.fetchall()
    cur.execute("SELECT * FROM suppliers ORDER BY name")
    suppliers_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template("stock.html", products=products_list, suppliers=suppliers_list)

if __name__ == "__main__":
    app.run(debug=True)
