# Databricks notebook source
# MAGIC %md
# MAGIC # PetInsure360 - Silver Layer Transformations
# MAGIC
# MAGIC **Purpose**: Transform Bronze data into clean, validated Silver tables
# MAGIC
# MAGIC **Transformations**:
# MAGIC - Data type casting
# MAGIC - Null handling
# MAGIC - Deduplication
# MAGIC - Data quality rules
# MAGIC - Standardization
# MAGIC
# MAGIC **Author**: Sunware Technologies

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import Window

# Storage configuration
storage_account = "petinsud7i43"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net"

# Create Silver database
spark.sql("CREATE DATABASE IF NOT EXISTS petinsure_silver")
spark.sql("USE petinsure_silver")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Helper Functions

# COMMAND ----------

def apply_data_quality_rules(df, table_name):
    """Apply standard data quality rules and add quality score column."""
    from functools import reduce
    from operator import add

    # Count nulls per row for key columns
    null_cols = [when(col(c).isNull(), lit(1)).otherwise(lit(0)) for c in df.columns if not c.startswith("_")]
    if len(null_cols) > 1:
        null_count_expr = reduce(add, null_cols)
    else:
        null_count_expr = null_cols[0] if null_cols else lit(0)

    df_with_quality = df \
        .withColumn("_null_count", null_count_expr) \
        .withColumn("_quality_score",
            when(col("_null_count") == 0, 100)
            .when(col("_null_count") <= 2, 80)
            .when(col("_null_count") <= 5, 60)
            .otherwise(40)
        ) \
        .withColumn("_silver_timestamp", current_timestamp())

    # Log quality metrics
    quality_stats = df_with_quality.agg(
        count("*").alias("total_records"),
        avg("_quality_score").alias("avg_quality_score"),
        sum(when(col("_quality_score") >= 80, 1).otherwise(0)).alias("high_quality_records")
    ).collect()[0]

    print(f"""
    {table_name} Quality Report:
    ---------------------------
    Total Records: {quality_stats['total_records']:,}
    Avg Quality Score: {quality_stats['avg_quality_score']:.1f}%
    High Quality Records (>=80%): {quality_stats['high_quality_records']:,}
    """)

    return df_with_quality

def deduplicate(df, key_columns, order_column):
    """Remove duplicates keeping the latest record."""
    window = Window.partitionBy(key_columns).orderBy(desc(order_column))
    return df \
        .withColumn("_row_num", row_number().over(window)) \
        .filter(col("_row_num") == 1) \
        .drop("_row_num")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Transform Customers → dim_customers

# COMMAND ----------

df_customers_bronze = spark.table("petinsure_bronze.customers_raw")

# Transformations
df_customers_silver = df_customers_bronze \
    .withColumn("customer_id", col("customer_id").cast(StringType())) \
    .withColumn("full_name", concat_ws(" ", col("first_name"), col("last_name"))) \
    .withColumn("email", lower(trim(col("email")))) \
    .withColumn("phone_clean", regexp_replace(col("phone"), "[^0-9]", "")) \
    .withColumn("date_of_birth", to_date(col("date_of_birth"), "yyyy-MM-dd")) \
    .withColumn("customer_since", to_date(col("customer_since"), "yyyy-MM-dd")) \
    .withColumn("age", floor(datediff(current_date(), col("date_of_birth")) / 365)) \
    .withColumn("tenure_months", floor(months_between(current_date(), col("customer_since")))) \
    .withColumn("state", upper(trim(col("state")))) \
    .withColumn("zip_code", lpad(col("zip_code"), 5, "0")) \
    .withColumn("is_valid_email", col("email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"))

# Deduplicate
df_customers_silver = deduplicate(df_customers_silver, ["customer_id"], "_ingestion_timestamp")

# Apply quality rules
df_customers_silver = apply_data_quality_rules(df_customers_silver, "dim_customers")

# Select final columns
df_customers_final = df_customers_silver.select(
    "customer_id",
    "first_name",
    "last_name",
    "full_name",
    "email",
    "is_valid_email",
    "phone",
    "phone_clean",
    "address_line1",
    "city",
    "state",
    "zip_code",
    "country",
    "date_of_birth",
    "age",
    "customer_since",
    "tenure_months",
    "preferred_contact",
    "marketing_opt_in",
    "referral_source",
    "customer_segment",
    "lifetime_value",
    "_quality_score",
    "_silver_timestamp"
)

# Write to Silver
df_customers_final.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Transform Pets → dim_pets

# COMMAND ----------

df_pets_bronze = spark.table("petinsure_bronze.pets_raw")

# Transformations
df_pets_silver = df_pets_bronze \
    .withColumn("pet_id", col("pet_id").cast(StringType())) \
    .withColumn("customer_id", col("customer_id").cast(StringType())) \
    .withColumn("pet_name", initcap(trim(col("pet_name")))) \
    .withColumn("species", initcap(trim(col("species")))) \
    .withColumn("breed", initcap(trim(col("breed")))) \
    .withColumn("date_of_birth", to_date(col("date_of_birth"), "yyyy-MM-dd")) \
    .withColumn("adoption_date", to_date(col("adoption_date"), "yyyy-MM-dd")) \
    .withColumn("age_years", floor(datediff(current_date(), col("date_of_birth")) / 365)) \
    .withColumn("age_months", floor(months_between(current_date(), col("date_of_birth")))) \
    .withColumn("weight_kg", round(col("weight_lbs") * 0.453592, 2)) \
    .withColumn("has_microchip", col("microchip_id").isNotNull()) \
    .withColumn("has_pre_existing", col("pre_existing_conditions").isNotNull()) \
    .withColumn("life_stage",
        when(col("age_years") < 1, "Puppy/Kitten")
        .when(col("age_years") < 7, "Adult")
        .when(col("age_years") < 10, "Senior")
        .otherwise("Geriatric")
    )

# Deduplicate
df_pets_silver = deduplicate(df_pets_silver, ["pet_id"], "_ingestion_timestamp")

# Apply quality rules
df_pets_silver = apply_data_quality_rules(df_pets_silver, "dim_pets")

# Write to Silver
df_pets_silver.select(
    "pet_id",
    "customer_id",
    "pet_name",
    "species",
    "breed",
    "gender",
    "date_of_birth",
    "age_years",
    "age_months",
    "life_stage",
    "weight_lbs",
    "weight_kg",
    "color",
    "microchip_id",
    "has_microchip",
    "is_neutered",
    "pre_existing_conditions",
    "has_pre_existing",
    "vaccination_status",
    "adoption_date",
    "is_active",
    "_quality_score",
    "_silver_timestamp"
).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_pets")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Transform Policies → dim_policies

# COMMAND ----------

df_policies_bronze = spark.table("petinsure_bronze.policies_raw")

# Transformations
df_policies_silver = df_policies_bronze \
    .withColumn("policy_id", col("policy_id").cast(StringType())) \
    .withColumn("effective_date", to_date(col("effective_date"), "yyyy-MM-dd")) \
    .withColumn("expiration_date", to_date(col("expiration_date"), "yyyy-MM-dd")) \
    .withColumn("cancellation_date", to_date(col("cancellation_date"), "yyyy-MM-dd")) \
    .withColumn("annual_premium", round(col("monthly_premium") * 12, 2)) \
    .withColumn("is_active", col("status") == "Active") \
    .withColumn("policy_age_months",
        floor(months_between(current_date(), col("effective_date")))
    ) \
    .withColumn("days_until_renewal",
        when(col("status") == "Active",
             datediff(col("expiration_date"), current_date()))
        .otherwise(lit(None))
    ) \
    .withColumn("plan_tier",
        when(col("plan_name") == "Basic", 1)
        .when(col("plan_name") == "Standard", 2)
        .when(col("plan_name") == "Premium", 3)
        .when(col("plan_name") == "Unlimited", 4)
        .otherwise(0)
    )

# Deduplicate
df_policies_silver = deduplicate(df_policies_silver, ["policy_id"], "_ingestion_timestamp")

# Apply quality rules
df_policies_silver = apply_data_quality_rules(df_policies_silver, "dim_policies")

# Write to Silver
df_policies_silver.select(
    "policy_id",
    "policy_number",
    "customer_id",
    "pet_id",
    "plan_name",
    "plan_tier",
    "monthly_premium",
    "annual_premium",
    "annual_deductible",
    "coverage_limit",
    "reimbursement_percentage",
    "effective_date",
    "expiration_date",
    "cancellation_date",
    "status",
    "is_active",
    "policy_age_months",
    "days_until_renewal",
    "payment_method",
    "payment_frequency",
    "waiting_period_days",
    "includes_wellness",
    "includes_dental",
    "includes_behavioral",
    "renewal_count",
    "_quality_score",
    "_silver_timestamp"
).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_policies")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Transform Vet Providers → dim_vet_providers

# COMMAND ----------

df_providers_bronze = spark.table("petinsure_bronze.vet_providers_raw")

# Transformations
df_providers_silver = df_providers_bronze \
    .withColumn("provider_id", col("provider_id").cast(StringType())) \
    .withColumn("provider_name", initcap(trim(col("provider_name")))) \
    .withColumn("state", upper(trim(col("state")))) \
    .withColumn("zip_code", lpad(col("zip_code"), 5, "0")) \
    .withColumn("rating_category",
        when(col("average_rating") >= 4.5, "Excellent")
        .when(col("average_rating") >= 4.0, "Good")
        .when(col("average_rating") >= 3.5, "Average")
        .otherwise("Below Average")
    ) \
    .withColumn("network_status",
        when(col("is_in_network"), "In-Network")
        .otherwise("Out-of-Network")
    )

# Deduplicate
df_providers_silver = deduplicate(df_providers_silver, ["provider_id"], "_ingestion_timestamp")

# Apply quality rules
df_providers_silver = apply_data_quality_rules(df_providers_silver, "dim_vet_providers")

# Write to Silver
df_providers_silver.select(
    "provider_id",
    "provider_name",
    "provider_type",
    "address",
    "city",
    "state",
    "zip_code",
    "phone",
    "email",
    "is_in_network",
    "network_status",
    "average_rating",
    "rating_category",
    "total_reviews",
    "accepts_emergency",
    "operating_hours",
    "specialties",
    "license_number",
    "_quality_score",
    "_silver_timestamp"
).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_vet_providers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Transform Claims → fact_claims

# COMMAND ----------

df_claims_bronze = spark.table("petinsure_bronze.claims_raw")

# Transformations
df_claims_silver = df_claims_bronze \
    .withColumn("claim_id", col("claim_id").cast(StringType())) \
    .withColumn("service_date", to_date(col("service_date"), "yyyy-MM-dd")) \
    .withColumn("submitted_date", to_date(col("submitted_date"), "yyyy-MM-dd")) \
    .withColumn("claim_amount", col("claim_amount").cast(DoubleType())) \
    .withColumn("deductible_applied", col("deductible_applied").cast(DoubleType())) \
    .withColumn("covered_amount", col("covered_amount").cast(DoubleType())) \
    .withColumn("paid_amount", col("paid_amount").cast(DoubleType())) \
    .withColumn("days_to_submit", datediff(col("submitted_date"), col("service_date"))) \
    .withColumn("processing_days", col("processing_days").cast(IntegerType())) \
    .withColumn("customer_out_of_pocket",
        col("claim_amount") - col("paid_amount")
    ) \
    .withColumn("reimbursement_rate",
        when(col("claim_amount") > 0,
             round(col("paid_amount") / col("claim_amount") * 100, 2))
        .otherwise(0)
    ) \
    .withColumn("claim_size_category",
        when(col("claim_amount") < 100, "Small (<$100)")
        .when(col("claim_amount") < 500, "Medium ($100-$500)")
        .when(col("claim_amount") < 2000, "Large ($500-$2000)")
        .otherwise("Major (>$2000)")
    ) \
    .withColumn("service_year", year(col("service_date"))) \
    .withColumn("service_month", month(col("service_date"))) \
    .withColumn("service_quarter", quarter(col("service_date")))

# Deduplicate
df_claims_silver = deduplicate(df_claims_silver, ["claim_id"], "_ingestion_timestamp")

# Apply quality rules
df_claims_silver = apply_data_quality_rules(df_claims_silver, "fact_claims")

# Write to Silver
df_claims_silver.select(
    "claim_id",
    "claim_number",
    "policy_id",
    "pet_id",
    "customer_id",
    "provider_id",
    "claim_type",
    "claim_category",
    "service_date",
    "service_year",
    "service_month",
    "service_quarter",
    "submitted_date",
    "days_to_submit",
    "claim_amount",
    "deductible_applied",
    "covered_amount",
    "paid_amount",
    "customer_out_of_pocket",
    "reimbursement_rate",
    "claim_size_category",
    "status",
    "denial_reason",
    "processing_days",
    "diagnosis_code",
    "treatment_notes",
    "invoice_number",
    "is_emergency",
    "is_recurring",
    "_quality_score",
    "_silver_timestamp"
).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("fact_claims")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Silver Layer

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify all silver tables
# MAGIC SELECT
# MAGIC     'dim_customers' as table_name, COUNT(*) as records, ROUND(AVG(_quality_score), 1) as avg_quality FROM petinsure_silver.dim_customers
# MAGIC UNION ALL
# MAGIC SELECT 'dim_pets', COUNT(*), ROUND(AVG(_quality_score), 1) FROM petinsure_silver.dim_pets
# MAGIC UNION ALL
# MAGIC SELECT 'dim_policies', COUNT(*), ROUND(AVG(_quality_score), 1) FROM petinsure_silver.dim_policies
# MAGIC UNION ALL
# MAGIC SELECT 'dim_vet_providers', COUNT(*), ROUND(AVG(_quality_score), 1) FROM petinsure_silver.dim_vet_providers
# MAGIC UNION ALL
# MAGIC SELECT 'fact_claims', COUNT(*), ROUND(AVG(_quality_score), 1) FROM petinsure_silver.fact_claims

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer Complete!
# MAGIC
# MAGIC Next: Run `03_gold_aggregations` notebook
