from typing import Dict
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, ArrayType


class SparkWriteDatabase:
    def __init__(self, spark: SparkSession, spark_config: Dict):
        self.spark = spark
        self.spark_config = spark_config

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
