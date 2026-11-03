CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    quantity INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 5,
    CHECK (price >= 0),
    CHECK (quantity >= 0),
    CHECK (reorder_level >= 0)
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    company VARCHAR(150),
    phone VARCHAR(15),
    email VARCHAR(100),
    address VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    supplier_id INT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    transaction_date DATE NOT NULL,
    CONSTRAINT fk_transaction_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_transaction_supplier FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    CHECK (quantity > 0),
    CHECK (transaction_type IN ('PURCHASE', 'SALE'))
);

-- Optional sample records for testing
INSERT INTO suppliers(name, company, phone, email, address)
VALUES ('ABC Suppliers', 'ABC Traders', '9876543210',
        'abc@example.com', 'Main Road')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO products(product_name, category, price, quantity, reorder_level)
VALUES ('Keyboard', 'Electronics', 650.00, 20, 5),
       ('Mouse', 'Electronics', 350.00, 15, 4),
       ('Notebook', 'Stationery', 50.00, 3, 10);
