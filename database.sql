-- Water Supply Management System - Database Setup
-- Run this in MySQL before running the Java application.

CREATE DATABASE IF NOT EXISTS water_supply_db;
USE water_supply_db;

-- Users table: powers Login (FR1) and role-based Dashboard access
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL,        -- stores SHA-256 hash, not plain text
    role VARCHAR(20) NOT NULL             -- Admin, Officer, Maintenance, Customer
);

-- Sample users. Passwords below are SHA-256 hashes of simple demo passwords.
-- admin   -> password: admin123
-- officer -> password: officer123
-- staff   -> password: staff123
-- customer-> password: customer123
-- (Generate your own hashes with: java PasswordUtil <password>)

INSERT INTO users (username, password, role) VALUES
('admin',    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Admin'),
('officer',  'a1c9c3c0b1f2f8c02e1b4a8c78e1a63c8c3d2c1c9c7c8d6e4f4c2c1c8d6e5f6a', 'Officer'),
('staff',    'b3e5c1f4a2c8d6e9f7a5c3b1d9e7f5a3c1b9d7e5f3a1c9b7d5e3f1a9c7b5d3e1', 'Maintenance'),
('customer', 'c4f6d2e5b3a9c7f1d8e6b4a2c9f7e5d3b1a9c7f5e3d1b9a7c5f3e1d9b7a5c3f1', 'Customer');

-- NOTE: The hash values above are placeholders/examples.
-- Before using this data, generate REAL hashes by running:
--     javac PasswordUtil.java
--     java PasswordUtil admin123
-- and paste the printed hash into the corresponding row.

-- Supporting tables from the SRS data requirements (section 6),
-- included so the schema matches the full system as you build it out.

CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    phone VARCHAR(20),
    meter_no VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS water_usage (
    usage_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    previous_reading DOUBLE,
    current_reading DOUBLE,
    consumption DOUBLE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE IF NOT EXISTS billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    bill_month DATE,
    amount DOUBLE,
    due_date DATE,
    payment_status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE IF NOT EXISTS maintenance (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    issue_type VARCHAR(50),
    request_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE IF NOT EXISTS complaint (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    complaint_type VARCHAR(50),
    description VARCHAR(500),
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);
