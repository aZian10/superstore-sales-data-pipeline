-- Silver Schema: DDL for clean dimensional entities and fact table

CREATE SCHEMA IF NOT EXISTS silver;

-- Dimension: Customers
CREATE TABLE IF NOT EXISTS silver.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Products (deduplicated by product_id)
CREATE TABLE IF NOT EXISTS silver.products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Geography
CREATE TABLE IF NOT EXISTS silver.geography (
    location_id SERIAL PRIMARY KEY,
    country VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_geography UNIQUE (country, region, state, city, postal_code)
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS silver.dim_date (
    date_id DATE PRIMARY KEY,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    day_of_week INT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Fact: Sales Transactions (one row per order line item)
CREATE TABLE IF NOT EXISTS silver.fact_sales (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL REFERENCES silver.dim_date(date_id),
    ship_date DATE NOT NULL REFERENCES silver.dim_date(date_id),
    ship_mode VARCHAR(50) NOT NULL,
    days_to_ship INT NOT NULL,
    customer_id VARCHAR(50) NOT NULL REFERENCES silver.customers(customer_id),
    product_id VARCHAR(50) NOT NULL REFERENCES silver.products(product_id),
    location_id INT NOT NULL REFERENCES silver.geography(location_id),
    sales NUMERIC(12, 4) NOT NULL,
    quantity INT NOT NULL,
    discount NUMERIC(5, 4) NOT NULL,
    profit NUMERIC(12, 4) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    is_profitable BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
