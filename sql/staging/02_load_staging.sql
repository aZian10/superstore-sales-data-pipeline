-- Staging Schema: Idempotent data standardization from raw.superstore to staging.superstore

TRUNCATE TABLE staging.superstore;

INSERT INTO staging.superstore (
    row_id,
    order_id,
    order_date,
    ship_date,
    ship_mode,
    customer_id,
    customer_name,
    segment,
    country,
    city,
    state,
    postal_code,
    region,
    product_id,
    category,
    sub_category,
    product_name,
    sales,
    quantity,
    discount,
    profit,
    loaded_at
)
SELECT
    "Row ID"::INT AS row_id,
    TRIM("Order ID") AS order_id,
    TO_DATE(TRIM("Order Date"), 'MM/DD/YYYY') AS order_date,
    TO_DATE(TRIM("Ship Date"), 'MM/DD/YYYY') AS ship_date,
    TRIM("Ship Mode") AS ship_mode,
    TRIM("Customer ID") AS customer_id,
    TRIM("Customer Name") AS customer_name,
    TRIM("Segment") AS segment,
    TRIM("Country") AS country,
    TRIM("City") AS city,
    TRIM("State") AS state,
    CASE
        WHEN TRIM("Postal Code"::TEXT) = '' OR "Postal Code" IS NULL THEN NULL
        ELSE LPAD(TRIM(SPLIT_PART("Postal Code"::TEXT, '.', 1)), 5, '0')
    END AS postal_code,
    TRIM("Region") AS region,
    TRIM("Product ID") AS product_id,
    TRIM("Category") AS category,
    TRIM("Sub-Category") AS sub_category,
    TRIM("Product Name") AS product_name,
    ROUND("Sales"::NUMERIC, 4) AS sales,
    "Quantity"::INT AS quantity,
    ROUND("Discount"::NUMERIC, 4) AS discount,
    ROUND("Profit"::NUMERIC, 4) AS profit,
    CURRENT_TIMESTAMP AS loaded_at
FROM raw.superstore;
