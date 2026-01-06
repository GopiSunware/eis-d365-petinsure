# Databricks notebook source
# MAGIC %md
# MAGIC # PetInsure360 - Bronze Layer Ingestion
# MAGIC
# MAGIC **Purpose**: Ingest raw data from ADLS Gen2 into Bronze Delta tables
# MAGIC
# MAGIC **Pattern**: Raw data → Bronze (as-is, with metadata)
# MAGIC
# MAGIC **Author**: Sunware Technologies

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Storage configuration
storage_account = "petinsud7i43"  # Update with your storage account name
container_bronze = "bronze"
container_raw = "raw"

# Mount point (or use direct ABFS path)
bronze_path = f"abfss://{container_bronze}@{storage_account}.dfs.core.windows.net"
raw_path = f"abfss://{container_raw}@{storage_account}.dfs.core.windows.net"

# Database
spark.sql("CREATE DATABASE IF NOT EXISTS petinsure_bronze")
spark.sql("USE petinsure_bronze")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Functions

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit, input_file_name
from pyspark.sql.types import *
from datetime import datetime

def add_bronze_metadata(df):
    """Add standard bronze layer metadata columns."""
    return df \
        .withColumn("_ingestion_timestamp", current_timestamp()) \
        .withColumn("_source_file", input_file_name()) \
        .withColumn("_batch_id", lit(datetime.now().strftime("%Y%m%d%H%M%S")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Ingest Customers (CSV)

# COMMAND ----------

# Schema for customers
customers_schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("email", StringType(), True),
    StructField("phone", StringType(), True),
    StructField("address_line1", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("zip_code", StringType(), True),
    StructField("country", StringType(), True),
    StructField("date_of_birth", StringType(), True),
    StructField("customer_since", StringType(), True),
    StructField("preferred_contact", StringType(), True),
    StructField("marketing_opt_in", BooleanType(), True),
    StructField("referral_source", StringType(), True),
    StructField("customer_segment", StringType(), True),
    StructField("lifetime_value", DoubleType(), True),
    StructField("created_at", StringType(), True),
    StructField("updated_at", StringType(), True)
])

# Read and write to Bronze
df_customers = spark.read \
    .option("header", "true") \
    .schema(customers_schema) \
    .csv(f"{raw_path}/customers.csv")

df_customers_bronze = add_bronze_metadata(df_customers)

df_customers_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("customers_raw")

print(f"Customers loaded: {df_customers_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Ingest Pets (CSV)

# COMMAND ----------

pets_schema = StructType([
    StructField("pet_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("pet_name", StringType(), True),
    StructField("species", StringType(), True),
    StructField("breed", StringType(), True),
    StructField("gender", StringType(), True),
    StructField("date_of_birth", StringType(), True),
    StructField("weight_lbs", DoubleType(), True),
    StructField("color", StringType(), True),
    StructField("microchip_id", StringType(), True),
    StructField("is_neutered", BooleanType(), True),
    StructField("pre_existing_conditions", StringType(), True),
    StructField("vaccination_status", StringType(), True),
    StructField("adoption_date", StringType(), True),
    StructField("is_active", BooleanType(), True),
    StructField("created_at", StringType(), True),
    StructField("updated_at", StringType(), True)
])

df_pets = spark.read \
    .option("header", "true") \
    .schema(pets_schema) \
    .csv(f"{raw_path}/pets.csv")

df_pets_bronze = add_bronze_metadata(df_pets)

df_pets_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("pets_raw")

print(f"Pets loaded: {df_pets_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Ingest Policies (CSV)

# COMMAND ----------

policies_schema = StructType([
    StructField("policy_id", StringType(), True),
    StructField("policy_number", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("pet_id", StringType(), True),
    StructField("plan_name", StringType(), True),
    StructField("monthly_premium", DoubleType(), True),
    StructField("annual_deductible", DoubleType(), True),
    StructField("coverage_limit", DoubleType(), True),
    StructField("reimbursement_percentage", DoubleType(), True),
    StructField("effective_date", StringType(), True),
    StructField("expiration_date", StringType(), True),
    StructField("status", StringType(), True),
    StructField("payment_method", StringType(), True),
    StructField("payment_frequency", StringType(), True),
    StructField("waiting_period_days", IntegerType(), True),
    StructField("includes_wellness", BooleanType(), True),
    StructField("includes_dental", BooleanType(), True),
    StructField("includes_behavioral", BooleanType(), True),
    StructField("cancellation_date", StringType(), True),
    StructField("renewal_count", IntegerType(), True),
    StructField("created_at", StringType(), True),
    StructField("updated_at", StringType(), True)
])

df_policies = spark.read \
    .option("header", "true") \
    .schema(policies_schema) \
    .csv(f"{raw_path}/policies.csv")

df_policies_bronze = add_bronze_metadata(df_policies)

df_policies_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("policies_raw")

print(f"Policies loaded: {df_policies_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Ingest Vet Providers (CSV)

# COMMAND ----------

providers_schema = StructType([
    StructField("provider_id", StringType(), True),
    StructField("provider_name", StringType(), True),
    StructField("provider_type", StringType(), True),
    StructField("address", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("zip_code", StringType(), True),
    StructField("phone", StringType(), True),
    StructField("email", StringType(), True),
    StructField("is_in_network", BooleanType(), True),
    StructField("average_rating", DoubleType(), True),
    StructField("total_reviews", IntegerType(), True),
    StructField("accepts_emergency", BooleanType(), True),
    StructField("operating_hours", StringType(), True),
    StructField("specialties", StringType(), True),
    StructField("license_number", StringType(), True),
    StructField("created_at", StringType(), True)
])

df_providers = spark.read \
    .option("header", "true") \
    .schema(providers_schema) \
    .csv(f"{raw_path}/vet_providers.csv")

df_providers_bronze = add_bronze_metadata(df_providers)

df_providers_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("vet_providers_raw")

print(f"Vet Providers loaded: {df_providers_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Ingest Claims (JSON Lines)

# COMMAND ----------

# Claims come as JSON lines (streaming-friendly format)
df_claims = spark.read \
    .json(f"{raw_path}/claims.jsonl")

df_claims_bronze = add_bronze_metadata(df_claims)

df_claims_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("claims_raw")

print(f"Claims loaded: {df_claims_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Layer

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify all bronze tables
# MAGIC SHOW TABLES IN petinsure_bronze;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Quick data quality check
# MAGIC SELECT
# MAGIC     'customers_raw' as table_name, COUNT(*) as record_count FROM petinsure_bronze.customers_raw
# MAGIC UNION ALL
# MAGIC SELECT 'pets_raw', COUNT(*) FROM petinsure_bronze.pets_raw
# MAGIC UNION ALL
# MAGIC SELECT 'policies_raw', COUNT(*) FROM petinsure_bronze.policies_raw
# MAGIC UNION ALL
# MAGIC SELECT 'claims_raw', COUNT(*) FROM petinsure_bronze.claims_raw
# MAGIC UNION ALL
# MAGIC SELECT 'vet_providers_raw', COUNT(*) FROM petinsure_bronze.vet_providers_raw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer Complete!
# MAGIC
# MAGIC Next: Run `02_silver_transformations` notebook
