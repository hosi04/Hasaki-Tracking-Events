WITH items AS (
    SELECT * FROM {{ ref('int_checkout_items') }}
),

aggregated AS (
    SELECT 
        session_id,
        user_id,
        timestamp,
        UPPER(product_name) AS product_name,
        product_brand,
        product_price,
        quantity,
        product_price * quantity AS total_value,
        is_high_value_item
    FROM items
)

SELECT * FROM aggregated
