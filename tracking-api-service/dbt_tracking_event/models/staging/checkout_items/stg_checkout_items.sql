WITH source AS (
    SELECT * 
    FROM {{ source('tracking_problem', 'checkout_items') }}
),

stg_checkout_items AS (
    SELECT 
        session_id,
        user_id,
        timestamp,
        product_name,
        product_brand,
        product_price,
        quantity

    FROM source
)

SELECT * FROM stg_checkout_items
