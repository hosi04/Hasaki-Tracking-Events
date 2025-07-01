WITH source AS (
    SELECT * 
    FROM {{ source('tracking_problem', 'event_add_to_cart') }}
),

stg_event_add_to_cart AS (
    SELECT 
        session_id,
        user_id,
        event_type,
        timestamp,
        productName,
        productBrand,
        productPrice,
        quantity,
        totalValue

    FROM source
)

SELECT * FROM stg_event_add_to_cart