from pyspark.sql.functions import from_json, col, to_json, to_utc_timestamp, from_unixtime, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType, ArrayType, TimestampType, MapType
from config.spark_config import SparkConnect
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

    # # Print out console to test
    # query = df_write_database.writeStream \
    #     .outputMode("append") \
    #     .format("console") \
    #     .option("truncate", False) \
    #     .start()
    # query.awaitTermination()

    # Write stream to clickhouse
    query = df_write_database.writeStream \
        .outputMode("append") \
        .foreachBatch(lambda batch_df, batch_id: batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
            .option("dbtable", "tracking_event_v02") \
            .option("user", "default") \
            .option("password", "") \
            .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
            .mode("append") \
            .save()) \
        .start()
    query.awaitTermination()

if __name__ == "__main__":
    main()

# PYTHONPATH=~/Prime/intern/tracking-event-project/etl-pipeline spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,com.clickhouse:clickhouse-jdbc:0.6.4,org.apache.httpcomponents.client5:httpclient5:5.3.1 ~/Prime/intern/tracking-event-project/etl-pipeline/src/spark/spark_main.py
