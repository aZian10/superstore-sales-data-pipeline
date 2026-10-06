-- Gold Schema: DDL for business analytical datasets and BI-ready views

CREATE SCHEMA IF NOT EXISTS gold;

-- 1. Daily Sales Performance
CREATE TABLE IF NOT EXISTS gold.daily_sales (
    order_date DATE PRIMARY KEY,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Monthly Sales Performance
CREATE TABLE IF NOT EXISTS gold.monthly_sales (
    year INT NOT NULL,
    month INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (year, month)
);

-- 3. Category & Sub-Category Performance
CREATE TABLE IF NOT EXISTS gold.category_performance (
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    loss_orders_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (category, sub_category)
);

-- 4. Product Performance & Rankings
CREATE TABLE IF NOT EXISTS gold.product_performance (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    is_loss_maker BOOLEAN NOT NULL,
    sales_rank INT NOT NULL,
    profit_rank INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Customer Performance & Lifetime Value
CREATE TABLE IF NOT EXISTS gold.customer_performance (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    first_order_date DATE NOT NULL,
    last_order_date DATE NOT NULL,
    customer_rank INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Regional & Geographic Performance
CREATE TABLE IF NOT EXISTS gold.regional_performance (
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    total_profit NUMERIC(14, 2) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (region, state)
);

-- 7. High-level Executive KPI Summary
CREATE TABLE IF NOT EXISTS gold.kpi_summary (
    metric_name VARCHAR(100) PRIMARY KEY,
    metric_value NUMERIC(16, 4) NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
