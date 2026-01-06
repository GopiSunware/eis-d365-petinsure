# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Lake Features Demo
# MAGIC
# MAGIC **For Client Presentation**
# MAGIC
# MAGIC This notebook demonstrates key Delta Lake capabilities:
# MAGIC - ACID Transactions
# MAGIC - Time Travel (Version History)
# MAGIC - Audit Trail
# MAGIC - Schema Details

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. View Table History (Audit Trail)
# MAGIC
# MAGIC Every change to a Delta table is logged with timestamp, user, and operation type.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY petinsure_gold.customer_360_view

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Time Travel - Query Previous Versions
# MAGIC
# MAGIC You can query any previous version of the data!

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query the current version
# MAGIC SELECT 'Current Version' as version, COUNT(*) as total_customers
# MAGIC FROM petinsure_gold.customer_360_view

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query Version 0 (first version)
# MAGIC SELECT 'Version 0' as version, COUNT(*) as total_customers
# MAGIC FROM petinsure_gold.customer_360_view VERSION AS OF 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Table Details
# MAGIC
# MAGIC Shows storage location, file format, and table properties.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL petinsure_gold.customer_360_view

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Sample Customer 360 Data

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     full_name,
# MAGIC     total_pets,
# MAGIC     total_policies,
# MAGIC     total_claims,
# MAGIC     total_annual_premium,
# MAGIC     customer_value_tier,
# MAGIC     customer_risk_score,
# MAGIC     churn_risk
# MAGIC FROM petinsure_gold.customer_360_view
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Monthly KPIs History

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY petinsure_gold.monthly_kpis

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM petinsure_gold.monthly_kpis ORDER BY year_month DESC LIMIT 12

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. All Gold Tables Summary

# COMMAND ----------

# MAGIC %sql
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
# MAGIC ## Key Talking Points
# MAGIC
# MAGIC 1. **ACID Transactions**: All writes are atomic - no partial updates
# MAGIC 2. **Time Travel**: Query or restore any previous version
# MAGIC 3. **Audit Trail**: Complete history of who changed what and when
# MAGIC 4. **Schema Enforcement**: Bad data is rejected automatically
# MAGIC 5. **Performance**: Z-ordering, data skipping, caching
