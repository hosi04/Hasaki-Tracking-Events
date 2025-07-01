WITH base AS (
    SELECT * FROM {{ ref('stg_checkout_items') }}
),

enriched AS (
    SELECT 
        session_id,
        user_id,
        timestamp,
        UPPER(product_name) AS product_name,
        product_brand,
        product_price,
        quantity,
        product_price * quantity AS total_value,
        CASE 
            WHEN product_price * quantity >= 1500000 THEN 1 
            ELSE 0
        END AS is_high_value_item
    FROM base
)

SELECT * FROM enriched