from databricks.connect import DatabricksSession


def main() -> None:
    spark = DatabricksSession.builder.serverless().profile("JAPAN_TOURISM").getOrCreate()

    print(f"Spark version: {spark.version}")

    result = spark.range(1, 6)

    print(f"Number of records: {result.count()}")

    result.show()

    spark.stop()


if __name__ == "__main__":
    main()
