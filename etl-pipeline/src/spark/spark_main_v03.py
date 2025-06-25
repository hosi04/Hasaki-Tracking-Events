from pyspark.sql.functions import from_json, col, to_json, to_utc_timestamp, from_unixtime, to_timestamp, explode
from pyspark.sql.types import StructType, StructField, StringType, LongType, ArrayType, TimestampType, MapType
from config.spark_config import SparkConnect

def write_to_clickhouse_tables(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    # Ghi toàn bộ vào bảng raw
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
        .option("dbtable", "tracking_event_v03") \
        .option("user", "default") \
        .option("password", "") \
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
        .mode("append") \
        .save()

    # Ghi riêng cho add_to_cart
    df_add_to_cart = batch_df.filter(col("event_type") == "add_to_cart") \
        .withColumn("data", from_json("data_json", StructType([
            StructField("productName", StringType()),
            StructField("productBrand", StringType()),
            StructField("productPrice", StringType()),
            StructField("quantity", StringType()),
            StructField("totalValue", StringType())
        ])))

    df_add_to_cart.select(
        "session_id", "user_id", "event_type", "timestamp",
        "data.productName", "data.productBrand", "data.productPrice",
        "data.quantity", "data.totalValue"
    ).write \
        .format("jdbc") \
        .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
        .option("dbtable", "event_add_to_cart") \
        .option("user", "default") \
        .option("password", "") \
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
        .mode("append") \
        .save()

    # Ghi riêng cho checkout_attempt
    df_checkout = batch_df.filter(col("event_type") == "checkout_attempt") \
        .withColumn("data", from_json("data_json", StructType([
            StructField("cartItems", StringType()),
            StructField("totalAmount", StringType()),
            StructField("itemCount", StringType()),
            StructField("totalQuantity", StringType())
        ])))

    df_checkout.select(
        "session_id", "user_id", "event_type", "timestamp",
        "data.totalAmount", "data.itemCount", "data.totalQuantity"
    ).write \
        .format("jdbc") \
        .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
        .option("dbtable", "event_checkout_attempt") \
        .option("user", "default") \
        .option("password", "") \
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
        .mode("append") \
        .save()

    # Ghi riêng cho checkout_items
    df_checkout = batch_df.filter(col("event_type") == "checkout_attempt")

    if not df_checkout.isEmpty():
        try:
            # cartItems là JSON string
            df_checkout_items = df_checkout \
                .withColumn("data", from_json("data_json", StructType([
                StructField("cartItems", StringType()),
                StructField("totalAmount", StringType()),
                StructField("itemCount", StringType()),
                StructField("totalQuantity", StringType())
            ]))) \
                .withColumn("cart_items_array", from_json("data.cartItems", ArrayType(StructType([
                StructField("name", StringType()),
                StructField("brand", StringType()),
                StructField("price", StringType()),
                StructField("quantity", StringType())
            ])))) \
                .where(col("cart_items_array").isNotNull()) \
                .withColumn("item", explode(col("cart_items_array"))) \
                .select(
                col("session_id"),
                col("user_id"),
                col("timestamp"),
                col("item.name").alias("product_name"),
                col("item.brand").alias("product_brand"),
                col("item.price").alias("product_price"),
                col("item.quantity").alias("quantity")
            )

            df_checkout_items.write \
                .format("jdbc") \
                .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
                .option("dbtable", "checkout_items") \
                .option("user", "default") \
                .option("password", "") \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .mode("append") \
                .save()

        except Exception as e:
            print(f"Error processing checkout_items: {str(e)}")
def main():

    jar_packages = [
        "com.clickhouse:clickhouse-jdbc:0.6.4",
        "org.apache.httpcomponents.client5:httpclient5:5.3.1"
    ]
    # Initial Spark
    spark = SparkConnect(
        app_name="thanhdz",
        master_url="local[*]",
        executor_cores=2,
        executor_memory="4g",
        driver_memory="2g",
        num_executors=3,
        jar_packages=jar_packages,
        log_level="WARN"
    ).spark
    spark.conf.set("spark.sql.session.timeZone", "Asia/Ho_Chi_Minh")

    # Read data from Kafka
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "test-topic") \
        .option("startingOffsets", "latest") \
        .load()

    schema = StructType([
        StructField("sessionId", StringType(), True),
        StructField("userId", StringType(), True),
        StructField("events", ArrayType(StructType([
            StructField("eventType", StringType(), True),
            StructField("sessionId", StringType(), True),
            StructField("data", MapType(StringType(), StringType()), True)
        ])), True),
        StructField("sessionInfo", StructType([
            StructField("startTime", LongType(), True),
            StructField("currentTime", LongType(), True),
        ]), True)
    ])

    # Step 1: Parse the raw Kafka (or JSON) value using schema
    df_parsed = df_raw.selectExpr("CAST(value AS STRING) AS json_str") \
        .select(from_json(col("json_str"), schema).alias("data"))

    # Step 2: Flatten the parsed struct into the desired output DataFrame
    df_write_database = df_parsed.select(
        col("data.sessionId").alias("session_id"),
        col("data.userId").alias("user_id"),
        col("data.events")[0]["eventType"].alias("event_type"),
        from_unixtime(col("data.sessionInfo.startTime") / 1000).alias("session_start_time"),
        from_unixtime(col("data.sessionInfo.currentTime") / 1000).alias("timestamp"),
        to_json(col("data.events")[0]["data"]).alias("data_json")
    )

    # Write stream to clickhouse
    query = df_write_database.writeStream \
        .outputMode("append") \
        .foreachBatch(write_to_clickhouse_tables) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()

# PYTHONPATH=~/Prime/intern/tracking-event-project/etl-pipeline spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,com.clickhouse:clickhouse-jdbc:0.6.4,org.apache.httpcomponents.client5:httpclient5:5.3.1 ~/Prime/intern/tracking-event-project/etl-pipeline/src/spark/spark_main.py
