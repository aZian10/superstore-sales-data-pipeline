-- Silver Schema: Idempotent dimensional loads and transformations

TRUNCATE TABLE silver.fact_sales, silver.customers, silver.products, silver.geography, silver.dim_date CASCADE;

-- 1. Populate dim_date (2013 to 2020)
INSERT INTO silver.dim_date (
    date_id,
    year,
    quarter,
    month,
    month_name,
    day,
    day_name,
    day_of_week,
    is_weekend
)
SELECT
    d::DATE AS date_id,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TO_CHAR(d, 'TMMonth') AS month_name,
    EXTRACT(DAY FROM d)::INT AS day,
    TO_CHAR(d, 'TMDay') AS day_name,
    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM GENERATE_SERIES('2013-01-01'::DATE, '2020-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- 2. Populate silver.customers (unique entities)
INSERT INTO silver.customers (
    customer_id,
    customer_name,
    segment,
    created_at
)
SELECT DISTINCT
    customer_id,
    customer_name,
    segment,
    CURRENT_TIMESTAMP AS created_at
FROM staging.superstore;

-- 3. Populate silver.products (deduplicate by product_id using frequency and length)
WITH product_freq AS (
    SELECT
        product_id,
        product_name,
        category,
        sub_category,
        COUNT(*) AS freq,
        LENGTH(product_name) AS len_name
    FROM staging.superstore
    GROUP BY product_id, product_name, category, sub_category
),
ranked_products AS (
    SELECT
        product_id,
        product_name,
        category,
        sub_category,
        ROW_NUMBER() OVER (
            PARTITION BY product_id 
            ORDER BY freq DESC, len_name DESC, product_name ASC
        ) AS rn
    FROM product_freq
)
INSERT INTO silver.products (
    product_id,
    product_name,
    category,
    sub_category,
    created_at
)
SELECT
    product_id,
    product_name,
    category,
    sub_category,
    CURRENT_TIMESTAMP AS created_at
FROM ranked_products
WHERE rn = 1;

-- 4. Populate silver.geography (unique locations)
INSERT INTO silver.geography (
    country,
    region,
    state,
    city,
    postal_code,
    created_at
)
SELECT DISTINCT
    country,
    region,
    state,
    city,
    postal_code,
    CURRENT_TIMESTAMP AS created_at
FROM staging.superstore;

-- 5. Populate silver.fact_sales
INSERT INTO silver.fact_sales (
    row_id,
    order_id,
    order_date,
    ship_date,
    ship_mode,
    days_to_ship,
    customer_id,
    product_id,
    location_id,
    sales,
    quantity,
    discount,
    profit,
    profit_margin,
    is_profitable,
    created_at
)
SELECT
    s.row_id,
    s.order_id,
    s.order_date,
    s.ship_date,
    s.ship_mode,
    (s.ship_date - s.order_date)::INT AS days_to_ship,
    s.customer_id,
    s.product_id,
    g.location_id,
    s.sales,
    s.quantity,
    s.discount,
    s.profit,
    CASE 
        WHEN s.sales > 0 THEN ROUND((s.profit / s.sales)::NUMERIC, 4)
        ELSE 0
    END AS profit_margin,
    (s.profit > 0) AS is_profitable,
    CURRENT_TIMESTAMP AS created_at
FROM staging.superstore s
JOIN silver.geography g ON 
    s.country = g.country
    AND s.region = g.region
    AND s.state = g.state
    AND s.city = g.city
    AND (s.postal_code = g.postal_code OR (s.postal_code IS NULL AND g.postal_code IS NULL));
