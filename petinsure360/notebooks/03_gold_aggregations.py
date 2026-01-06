# Databricks notebook source
# MAGIC %md
# MAGIC # PetInsure360 - Gold Layer Aggregations
# MAGIC
# MAGIC **Purpose**: Create business-ready aggregations and CDP views
# MAGIC
# MAGIC **Gold Tables**:
# MAGIC - customer_360_view (CDP - Customer Data Platform)
# MAGIC - claims_analytics (Claims performance metrics)
# MAGIC - risk_scoring (Risk assessment)
# MAGIC - cross_sell_recommendations (Upsell/cross-sell opportunities)
# MAGIC - provider_performance (Vet provider analytics)
# MAGIC - monthly_kpis (Executive dashboard metrics)
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
gold_path = f"abfss://gold@{storage_account}.dfs.core.windows.net"

# Create Gold database
spark.sql("CREATE DATABASE IF NOT EXISTS petinsure_gold")
spark.sql("USE petinsure_gold")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Silver Tables

# COMMAND ----------

df_customers = spark.table("petinsure_silver.dim_customers")
df_pets = spark.table("petinsure_silver.dim_pets")
df_policies = spark.table("petinsure_silver.dim_policies")
df_claims = spark.table("petinsure_silver.fact_claims")
df_providers = spark.table("petinsure_silver.dim_vet_providers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Customer 360 View (CDP - Unified Customer View)
# MAGIC
# MAGIC This is the **core CDP** combining all customer touchpoints into a single view.

# COMMAND ----------

# Aggregate pet data per customer
pets_agg = df_pets \
    .groupBy("customer_id") \
    .agg(
        count("*").alias("total_pets"),
        sum(when(col("species") == "Dog", 1).otherwise(0)).alias("dog_count"),
        sum(when(col("species") == "Cat", 1).otherwise(0)).alias("cat_count"),
        sum(when(col("is_active"), 1).otherwise(0)).alias("active_pets"),
        avg("age_years").alias("avg_pet_age"),
        collect_set("species").alias("pet_species_list"),
        collect_set("breed").alias("pet_breeds_list"),
        sum(when(col("has_pre_existing"), 1).otherwise(0)).alias("pets_with_conditions")
    )

# Aggregate policy data per customer
policies_agg = df_policies \
    .groupBy("customer_id") \
    .agg(
        count("*").alias("total_policies"),
        sum(when(col("is_active"), 1).otherwise(0)).alias("active_policies"),
        sum("annual_premium").alias("total_annual_premium"),
        avg("annual_premium").alias("avg_annual_premium"),
        max("plan_tier").alias("highest_plan_tier"),
        min("effective_date").alias("first_policy_date"),
        max("effective_date").alias("latest_policy_date"),
        avg("renewal_count").alias("avg_renewal_count"),
        sum(when(col("includes_wellness"), 1).otherwise(0)).alias("wellness_coverage_count"),
        sum(when(col("includes_dental"), 1).otherwise(0)).alias("dental_coverage_count"),
        min("days_until_renewal").alias("min_days_until_renewal")
    )

# Aggregate claims data per customer
claims_agg = df_claims \
    .groupBy("customer_id") \
    .agg(
        count("*").alias("total_claims"),
        sum("claim_amount").alias("total_claim_amount"),
        sum("paid_amount").alias("total_paid_amount"),
        avg("claim_amount").alias("avg_claim_amount"),
        max("claim_amount").alias("max_claim_amount"),
        sum(when(col("status") == "Denied", 1).otherwise(0)).alias("denied_claims"),
        sum(when(col("is_emergency"), 1).otherwise(0)).alias("emergency_claims"),
        avg("processing_days").alias("avg_processing_days"),
        min("service_date").alias("first_claim_date"),
        max("service_date").alias("last_claim_date"),
        countDistinct("claim_category").alias("unique_claim_categories"),
        collect_set("claim_category").alias("claim_categories_list")
    )

# Build Customer 360 View
customer_360 = df_customers \
    .join(pets_agg, "customer_id", "left") \
    .join(policies_agg, "customer_id", "left") \
    .join(claims_agg, "customer_id", "left") \
    .withColumn("loss_ratio",
        when(col("total_annual_premium") > 0,
             round(col("total_paid_amount") / col("total_annual_premium") * 100, 2))
        .otherwise(0)
    ) \
    .withColumn("claims_per_pet",
        when(col("total_pets") > 0,
             round(col("total_claims") / col("total_pets"), 2))
        .otherwise(0)
    ) \
    .withColumn("customer_risk_score",
        when(col("loss_ratio") > 150, "High Risk")
        .when(col("loss_ratio") > 100, "Medium Risk")
        .when(col("loss_ratio") > 50, "Low Risk")
        .otherwise("Very Low Risk")
    ) \
    .withColumn("customer_value_tier",
        when(col("total_annual_premium") > 1000, "Platinum")
        .when(col("total_annual_premium") > 500, "Gold")
        .when(col("total_annual_premium") > 200, "Silver")
        .otherwise("Bronze")
    ) \
    .withColumn("engagement_score",
        (
            coalesce(col("total_claims"), lit(0)) * 10 +
            coalesce(col("avg_renewal_count"), lit(0)) * 20 +
            coalesce(col("tenure_months"), lit(0)) * 2 +
            when(col("marketing_opt_in"), 10).otherwise(0)
        )
    ) \
    .withColumn("churn_risk",
        when(col("min_days_until_renewal") < 30, "High")
        .when(col("min_days_until_renewal") < 60, "Medium")
        .when(col("active_policies") == 0, "Churned")
        .otherwise("Low")
    ) \
    .withColumn("_gold_timestamp", current_timestamp())

# Write Customer 360 to Gold (ADLS path for Synapse access)
customer_360_path = f"{gold_path}/customer_360_view"
customer_360.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(customer_360_path)

# Also create managed table pointing to this path
spark.sql(f"CREATE TABLE IF NOT EXISTS customer_360_view USING DELTA LOCATION '{customer_360_path}'")

print(f"Customer 360 created: {customer_360.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Claims Analytics

# COMMAND ----------

# Claims analytics with time-based aggregations
claims_analytics = df_claims \
    .join(df_policies.select("policy_id", "plan_name", "plan_tier"), "policy_id", "left") \
    .join(df_pets.select("pet_id", "species", "breed", "life_stage"), "pet_id", "left") \
    .join(df_providers.select("provider_id", "provider_name", "is_in_network", "provider_type"), "provider_id", "left") \
    .withColumn("service_year_month", date_format(col("service_date"), "yyyy-MM")) \
    .withColumn("network_savings",
        when(col("is_in_network"),
             col("claim_amount") * 0.15)  # Assume 15% network discount
        .otherwise(0)
    ) \
    .withColumn("_gold_timestamp", current_timestamp())

# Write to ADLS for Synapse access
claims_analytics_path = f"{gold_path}/claims_analytics"
claims_analytics.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(claims_analytics_path)

spark.sql(f"CREATE TABLE IF NOT EXISTS claims_analytics USING DELTA LOCATION '{claims_analytics_path}'")

print(f"Claims Analytics created: {claims_analytics.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Monthly KPIs (Executive Dashboard)

# COMMAND ----------

# Aggregate KPIs by month
monthly_kpis = df_claims \
    .withColumn("year_month", date_format(col("service_date"), "yyyy-MM")) \
    .groupBy("year_month") \
    .agg(
        count("*").alias("total_claims"),
        countDistinct("customer_id").alias("unique_customers"),
        countDistinct("pet_id").alias("unique_pets"),
        sum("claim_amount").alias("total_claim_amount"),
        sum("paid_amount").alias("total_paid_amount"),
        avg("claim_amount").alias("avg_claim_amount"),
        avg("processing_days").alias("avg_processing_days"),
        sum(when(col("status") == "Approved", 1).otherwise(0)).alias("approved_claims"),
        sum(when(col("status") == "Denied", 1).otherwise(0)).alias("denied_claims"),
        sum(when(col("is_emergency"), 1).otherwise(0)).alias("emergency_claims")
    ) \
    .withColumn("approval_rate", round(col("approved_claims") / col("total_claims") * 100, 2)) \
    .withColumn("denial_rate", round(col("denied_claims") / col("total_claims") * 100, 2)) \
    .withColumn("loss_ratio", round(col("total_paid_amount") / col("total_claim_amount") * 100, 2)) \
    .withColumn("_gold_timestamp", current_timestamp()) \
    .orderBy("year_month")

# Write to ADLS for Synapse access
monthly_kpis_path = f"{gold_path}/monthly_kpis"
monthly_kpis.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(monthly_kpis_path)

spark.sql(f"CREATE TABLE IF NOT EXISTS monthly_kpis USING DELTA LOCATION '{monthly_kpis_path}'")

print(f"Monthly KPIs created: {monthly_kpis.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Cross-Sell Recommendations

# COMMAND ----------

# Identify cross-sell opportunities
customer_360_df = spark.table("petinsure_gold.customer_360_view")

cross_sell = customer_360_df \
    .select(
        "customer_id",
        "full_name",
        "email",
        "total_pets",
        "active_policies",
        "highest_plan_tier",
        "wellness_coverage_count",
        "dental_coverage_count",
        "total_annual_premium",
        "customer_value_tier",
        "loss_ratio"
    ) \
    .withColumn("upgrade_opportunity",
        when((col("highest_plan_tier") < 3) & (col("loss_ratio") < 80), True)
        .otherwise(False)
    ) \
    .withColumn("wellness_opportunity",
        when((col("wellness_coverage_count") == 0) & (col("active_policies") > 0), True)
        .otherwise(False)
    ) \
    .withColumn("dental_opportunity",
        when((col("dental_coverage_count") == 0) & (col("active_policies") > 0), True)
        .otherwise(False)
    ) \
    .withColumn("multi_pet_opportunity",
        when((col("total_pets") > col("active_policies")) & (col("active_policies") > 0), True)
        .otherwise(False)
    ) \
    .withColumn("recommendation",
        when(col("upgrade_opportunity"), "Plan Upgrade")
        .when(col("wellness_opportunity"), "Add Wellness Coverage")
        .when(col("dental_opportunity"), "Add Dental Coverage")
        .when(col("multi_pet_opportunity"), "Insure Additional Pets")
        .otherwise("Retain & Engage")
    ) \
    .withColumn("estimated_revenue_opportunity",
        when(col("upgrade_opportunity"), col("total_annual_premium") * 0.5)
        .when(col("wellness_opportunity"), lit(120))
        .when(col("dental_opportunity"), lit(180))
        .when(col("multi_pet_opportunity"), col("total_annual_premium") * 0.8)
        .otherwise(0)
    ) \
    .withColumn("priority_score",
        col("estimated_revenue_opportunity") * (100 - col("loss_ratio")) / 100
    ) \
    .withColumn("_gold_timestamp", current_timestamp())

# Write to ADLS for Synapse access
cross_sell_path = f"{gold_path}/cross_sell_recommendations"
cross_sell.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(cross_sell_path)

spark.sql(f"CREATE TABLE IF NOT EXISTS cross_sell_recommendations USING DELTA LOCATION '{cross_sell_path}'")

print(f"Cross-sell recommendations created: {cross_sell.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Provider Performance Analytics

# COMMAND ----------

provider_performance = df_claims \
    .join(df_providers, "provider_id", "left") \
    .groupBy(
        "provider_id",
        "provider_name",
        "provider_type",
        "city",
        "state",
        "is_in_network",
        "average_rating"
    ) \
    .agg(
        count("*").alias("total_claims"),
        countDistinct("customer_id").alias("unique_customers"),
        sum("claim_amount").alias("total_billed"),
        sum("paid_amount").alias("total_paid"),
        avg("claim_amount").alias("avg_claim_amount"),
        avg("processing_days").alias("avg_processing_days"),
        sum(when(col("status") == "Denied", 1).otherwise(0)).alias("denied_claims"),
        sum(when(col("is_emergency"), 1).otherwise(0)).alias("emergency_visits")
    ) \
    .withColumn("denial_rate", round(col("denied_claims") / col("total_claims") * 100, 2)) \
    .withColumn("avg_cost_per_visit", round(col("total_billed") / col("total_claims"), 2)) \
    .withColumn("provider_tier",
        when((col("average_rating") >= 4.5) & (col("denial_rate") < 10), "Preferred")
        .when((col("average_rating") >= 4.0) & (col("denial_rate") < 20), "Standard")
        .otherwise("Review Required")
    ) \
    .withColumn("_gold_timestamp", current_timestamp())

# Write to ADLS for Synapse access
provider_performance_path = f"{gold_path}/provider_performance"
provider_performance.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(provider_performance_path)

spark.sql(f"CREATE TABLE IF NOT EXISTS provider_performance USING DELTA LOCATION '{provider_performance_path}'")

print(f"Provider Performance created: {provider_performance.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Risk Scoring Model

# COMMAND ----------

# Risk scoring based on historical claims patterns
risk_scoring = customer_360_df \
    .select(
        "customer_id",
        "full_name",
        "total_pets",
        "avg_pet_age",
        "pets_with_conditions",
        "total_claims",
        "total_claim_amount",
        "total_paid_amount",
        "emergency_claims",
        "loss_ratio",
        "tenure_months",
        "highest_plan_tier"
    ) \
    .withColumn("pet_age_risk",
        when(col("avg_pet_age") > 10, 30)
        .when(col("avg_pet_age") > 7, 20)
        .when(col("avg_pet_age") > 4, 10)
        .otherwise(5)
    ) \
    .withColumn("condition_risk",
        when(col("pets_with_conditions") > 0, col("pets_with_conditions") * 15)
        .otherwise(0)
    ) \
    .withColumn("claims_frequency_risk",
        when(col("total_claims") / greatest(col("tenure_months"), lit(1)) > 2, 25)
        .when(col("total_claims") / greatest(col("tenure_months"), lit(1)) > 1, 15)
        .otherwise(5)
    ) \
    .withColumn("emergency_risk",
        when(col("emergency_claims") > 3, 20)
        .when(col("emergency_claims") > 1, 10)
        .otherwise(0)
    ) \
    .withColumn("loss_ratio_risk",
        when(col("loss_ratio") > 150, 30)
        .when(col("loss_ratio") > 100, 20)
        .when(col("loss_ratio") > 70, 10)
        .otherwise(0)
    ) \
    .withColumn("total_risk_score",
        col("pet_age_risk") +
        col("condition_risk") +
        col("claims_frequency_risk") +
        col("emergency_risk") +
        col("loss_ratio_risk")
    ) \
    .withColumn("risk_category",
        when(col("total_risk_score") > 80, "Very High")
        .when(col("total_risk_score") > 60, "High")
        .when(col("total_risk_score") > 40, "Medium")
        .when(col("total_risk_score") > 20, "Low")
        .otherwise("Very Low")
    ) \
    .withColumn("recommended_action",
        when(col("risk_category") == "Very High", "Review for rate adjustment")
        .when(col("risk_category") == "High", "Monitor closely")
        .when(col("risk_category").isin("Low", "Very Low"), "Candidate for loyalty rewards")
        .otherwise("Standard monitoring")
    ) \
    .withColumn("_gold_timestamp", current_timestamp())

# Write to ADLS for Synapse access
risk_scoring_path = f"{gold_path}/risk_scoring"
risk_scoring.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(risk_scoring_path)

spark.sql(f"CREATE TABLE IF NOT EXISTS risk_scoring USING DELTA LOCATION '{risk_scoring_path}'")

print(f"Risk Scoring created: {risk_scoring.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Gold Layer

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Summary of all Gold tables
# MAGIC SELECT 'customer_360_view' as table_name, COUNT(*) as records FROM petinsure_gold.customer_360_view
# MAGIC UNION ALL
# MAGIC SELECT 'claims_analytics', COUNT(*) FROM petinsure_gold.claims_analytics
# MAGIC UNION ALL
# MAGIC SELECT 'monthly_kpis', COUNT(*) FROM petinsure_gold.monthly_kpis
# MAGIC UNION ALL
# MAGIC SELECT 'cross_sell_recommendations', COUNT(*) FROM petinsure_gold.cross_sell_recommendations
# MAGIC UNION ALL
# MAGIC SELECT 'provider_performance', COUNT(*) FROM petinsure_gold.provider_performance
# MAGIC UNION ALL
# MAGIC SELECT 'risk_scoring', COUNT(*) FROM petinsure_gold.risk_scoring

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Queries for Power BI

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Executive KPI Summary
# MAGIC SELECT
# MAGIC     year_month,
# MAGIC     total_claims,
# MAGIC     total_paid_amount,
# MAGIC     approval_rate,
# MAGIC     avg_processing_days
# MAGIC FROM petinsure_gold.monthly_kpis
# MAGIC ORDER BY year_month DESC
# MAGIC LIMIT 12;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top Cross-Sell Opportunities
# MAGIC SELECT
# MAGIC     full_name,
# MAGIC     customer_value_tier,
# MAGIC     recommendation,
# MAGIC     estimated_revenue_opportunity,
# MAGIC     priority_score
# MAGIC FROM petinsure_gold.cross_sell_recommendations
# MAGIC WHERE estimated_revenue_opportunity > 0
# MAGIC ORDER BY priority_score DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- High Risk Customers
# MAGIC SELECT
# MAGIC     full_name,
# MAGIC     total_risk_score,
# MAGIC     risk_category,
# MAGIC     loss_ratio,
# MAGIC     recommended_action
# MAGIC FROM petinsure_gold.risk_scoring
# MAGIC WHERE risk_category IN ('High', 'Very High')
# MAGIC ORDER BY total_risk_score DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer Complete!
# MAGIC
# MAGIC **Tables ready for Power BI and Synapse:**
# MAGIC - `petinsure_gold.customer_360_view` - CDP unified customer view
# MAGIC - `petinsure_gold.claims_analytics` - Detailed claims with dimensions
# MAGIC - `petinsure_gold.monthly_kpis` - Executive metrics
# MAGIC - `petinsure_gold.cross_sell_recommendations` - Upsell opportunities
# MAGIC - `petinsure_gold.provider_performance` - Vet network analytics
# MAGIC - `petinsure_gold.risk_scoring` - Customer risk assessment
# MAGIC
# MAGIC Next: Connect Synapse Serverless and Power BI
