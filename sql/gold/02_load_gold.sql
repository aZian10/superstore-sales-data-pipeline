-- Gold Schema: Idempotent aggregation and business metric calculations

TRUNCATE TABLE 
    gold.daily_sales,
    gold.monthly_sales,
    gold.category_performance,
    gold.product_performance,
    gold.customer_performance,
    gold.regional_performance,
    gold.kpi_summary;

-- 1. Daily Sales
INSERT INTO gold.daily_sales (
    order_date,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    avg_order_value,
    profit_margin,
    created_at
)
SELECT
    order_date,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS total_quantity,
    ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0), 4) AS profit_margin,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales
GROUP BY order_date;

-- 2. Monthly Sales
INSERT INTO gold.monthly_sales (
    year,
    month,
    year_month,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    avg_order_value,
    profit_margin,
    created_at
)
SELECT
    d.year,
    d.month,
    TO_CHAR(d.date_id, 'YYYY-MM') AS year_month,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales f
JOIN silver.dim_date d ON f.order_date = d.date_id
GROUP BY d.year, d.month, TO_CHAR(d.date_id, 'YYYY-MM');

-- 3. Category & Sub-Category Performance
INSERT INTO gold.category_performance (
    category,
    sub_category,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    profit_margin,
    loss_orders_count,
    created_at
)
SELECT
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    COUNT(CASE WHEN f.profit < 0 THEN 1 END) AS loss_orders_count,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales f
JOIN silver.products p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category;

-- 4. Product Performance & Rankings
INSERT INTO gold.product_performance (
    product_id,
    product_name,
    category,
    sub_category,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    profit_margin,
    is_loss_maker,
    sales_rank,
    profit_rank,
    created_at
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    (SUM(f.profit) < 0) AS is_loss_maker,
    DENSE_RANK() OVER (ORDER BY SUM(f.sales) DESC) AS sales_rank,
    DENSE_RANK() OVER (ORDER BY SUM(f.profit) DESC) AS profit_rank,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales f
JOIN silver.products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category;

-- 5. Customer Performance & Lifetime Value
INSERT INTO gold.customer_performance (
    customer_id,
    customer_name,
    segment,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    avg_order_value,
    profit_margin,
    first_order_date,
    last_order_date,
    customer_rank,
    created_at
)
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    MIN(f.order_date) AS first_order_date,
    MAX(f.order_date) AS last_order_date,
    DENSE_RANK() OVER (ORDER BY SUM(f.sales) DESC) AS customer_rank,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales f
JOIN silver.customers c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment;

-- 6. Regional Performance
INSERT INTO gold.regional_performance (
    region,
    state,
    total_sales,
    total_profit,
    total_orders,
    total_quantity,
    avg_order_value,
    profit_margin,
    created_at
)
SELECT
    g.region,
    g.state,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    CURRENT_TIMESTAMP AS created_at
FROM silver.fact_sales f
JOIN silver.geography g ON f.location_id = g.location_id
GROUP BY g.region, g.state;

-- 7. High-Level Executive KPI Summary
INSERT INTO gold.kpi_summary (metric_name, metric_value, description)
SELECT
    'total_sales',
    ROUND(SUM(sales), 2),
    'Total Gross Sales across all orders'
FROM silver.fact_sales
UNION ALL
SELECT
    'total_profit',
    ROUND(SUM(profit), 2),
    'Total Net Profit across all transactions'
FROM silver.fact_sales
UNION ALL
SELECT
    'total_orders',
    COUNT(DISTINCT order_id),
    'Total Unique Orders processed'
FROM silver.fact_sales
UNION ALL
SELECT
    'total_quantity',
    SUM(quantity),
    'Total Units of products sold'
FROM silver.fact_sales
UNION ALL
SELECT
    'average_order_value',
    ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2),
    'Average Order Value (Total Sales / Total Orders)'
FROM silver.fact_sales
UNION ALL
SELECT
    'overall_profit_margin',
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2),
    'Overall Profit Margin percentage (Total Profit / Total Sales * 100)'
FROM silver.fact_sales
UNION ALL
SELECT
    'loss_making_products_count',
    COUNT(*),
    'Total distinct products yielding negative net profit'
FROM gold.product_performance
WHERE is_loss_maker = TRUE;
