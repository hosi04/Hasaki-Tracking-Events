from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType
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

    # Read data from Kafka
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "test-topic") \
        .option("startingOffsets", "latest") \
        .load()

    schema = StructType([
        StructField("sessionId", StringType(), True),
        StructField("userId", StringType(), True)
    ])

    # Parse JSON và extract 2 field
    df_parsed = df_raw.selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), schema).alias("data")) \
        .select(
        col("data.sessionId").alias("session_id"),
        col("data.userId").alias("user_id")
    )

    # Write stream to clickhouse
    query = df_parsed.writeStream \
        .outputMode("append") \
        .foreachBatch(lambda batch_df, batch_id: batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:clickhouse://localhost:8123/tracking_problem") \
            .option("dbtable", "tracking_event") \
            .option("user", "default") \
            .option("password", "") \
            .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
            .mode("append") \
            .save()) \
        .start()
    query.awaitTermination()

    # # Print out console to test
    # query = df_parsed.writeStream \s
    #     .outputMode("append") \
    #     .format("console") \
    #     .option("truncate", False) \
    #     .start()
    # query.awaitTermination()

if __name__ == "__main__":
    main()

  # // Lenh chay moi nhat
  # PYTHONPATH=~/Prime/Intern/Pycharm_project/Tracking_problem \
  # spark-submit \
  # --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,com.clickhouse:clickhouse-jdbc:0.6.4,org.apache.httpcomponents.client5:httpclient5:5.3.1 \
  # spark/spark_main.py
