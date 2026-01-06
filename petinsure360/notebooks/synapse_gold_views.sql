-- =============================================================================
-- PetInsure360 - Synapse Serverless SQL Views
-- =============================================================================
-- Purpose: Create external tables/views over Delta Lake Gold layer
-- This enables Power BI DirectQuery and ad-hoc SQL analysis
--
-- Author: Gopinath Varadharajan
-- =============================================================================

-- Create database for Gold layer access
CREATE DATABASE IF NOT EXISTS petinsure_gold;
GO

USE petinsure_gold;
GO

-- =============================================================================
-- CREDENTIAL & DATA SOURCE SETUP
-- =============================================================================

-- Create credential for storage access (use Managed Identity in production)
-- For demo, we'll use storage account key
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'YourStrongPassword123!';
GO

-- Create database scoped credential
CREATE DATABASE SCOPED CREDENTIAL StorageCredential
WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
SECRET = '<YOUR-SAS-TOKEN>';  -- Replace with actual SAS token
GO

-- Create external data source pointing to Gold container
CREATE EXTERNAL DATA SOURCE GoldLake
WITH (
    LOCATION = 'https://petinsud7i43.dfs.core.windows.net/gold',
    CREDENTIAL = StorageCredential
);
GO

-- =============================================================================
-- EXTERNAL FILE FORMAT FOR DELTA
-- =============================================================================

CREATE EXTERNAL FILE FORMAT DeltaFormat
WITH (
    FORMAT_TYPE = DELTA
);
GO

-- =============================================================================
-- GOLD LAYER VIEWS (Reading Delta Tables)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Customer 360 View (CDP)
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_customer_360 AS
SELECT *
FROM OPENROWSET(
    BULK 'customer_360_view',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS customer_360;
GO

-- -----------------------------------------------------------------------------
-- 2. Claims Analytics
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_claims_analytics AS
SELECT *
FROM OPENROWSET(
    BULK 'claims_analytics',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS claims;
GO

-- -----------------------------------------------------------------------------
-- 3. Monthly KPIs
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_monthly_kpis AS
SELECT *
FROM OPENROWSET(
    BULK 'monthly_kpis',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS kpis;
GO

-- -----------------------------------------------------------------------------
-- 4. Cross-Sell Recommendations
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_cross_sell AS
SELECT *
FROM OPENROWSET(
    BULK 'cross_sell_recommendations',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS cross_sell;
GO

-- -----------------------------------------------------------------------------
-- 5. Provider Performance
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_provider_performance AS
SELECT *
FROM OPENROWSET(
    BULK 'provider_performance',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS providers;
GO

-- -----------------------------------------------------------------------------
-- 6. Risk Scoring
-- -----------------------------------------------------------------------------
CREATE OR ALTER VIEW vw_risk_scoring AS
SELECT *
FROM OPENROWSET(
    BULK 'risk_scoring',
    DATA_SOURCE = 'GoldLake',
    FORMAT = 'DELTA'
) AS risk;
GO

-- =============================================================================
-- SEMANTIC LAYER VIEWS (For Power BI)
-- =============================================================================

-- Executive Dashboard View
CREATE OR ALTER VIEW vw_executive_dashboard AS
SELECT
    year_month,
    total_claims,
    unique_customers,
    total_claim_amount,
    total_paid_amount,
    approval_rate,
    denial_rate,
    avg_processing_days,
    loss_ratio,
    -- Calculate MoM change (requires LAG which works in Synapse)
    LAG(total_claims) OVER (ORDER BY year_month) as prev_month_claims,
    CASE
        WHEN LAG(total_claims) OVER (ORDER BY year_month) > 0
        THEN ROUND((total_claims - LAG(total_claims) OVER (ORDER BY year_month)) * 100.0 /
             LAG(total_claims) OVER (ORDER BY year_month), 2)
        ELSE 0
    END as claims_growth_pct
FROM vw_monthly_kpis;
GO

-- Customer Segmentation View
CREATE OR ALTER VIEW vw_customer_segments AS
SELECT
    customer_value_tier,
    customer_risk_score,
    COUNT(*) as customer_count,
    AVG(total_annual_premium) as avg_premium,
    AVG(total_claims) as avg_claims,
    AVG(loss_ratio) as avg_loss_ratio,
    SUM(total_annual_premium) as total_premium_value
FROM vw_customer_360
GROUP BY customer_value_tier, customer_risk_score;
GO

-- Claims by Category View
CREATE OR ALTER VIEW vw_claims_by_category AS
SELECT
    claim_category,
    species,
    COUNT(*) as claim_count,
    SUM(claim_amount) as total_amount,
    AVG(claim_amount) as avg_amount,
    SUM(paid_amount) as total_paid,
    AVG(processing_days) as avg_processing_days
FROM vw_claims_analytics
GROUP BY claim_category, species;
GO

-- =============================================================================
-- SAMPLE QUERIES FOR TESTING
-- =============================================================================

-- Test Customer 360
-- SELECT TOP 10 * FROM vw_customer_360;

-- Test Monthly KPIs
-- SELECT * FROM vw_executive_dashboard ORDER BY year_month DESC;

-- Test Customer Segments
-- SELECT * FROM vw_customer_segments ORDER BY total_premium_value DESC;

-- High Value Customers with Upsell Opportunities
-- SELECT
--     full_name,
--     email,
--     customer_value_tier,
--     total_annual_premium,
--     recommendation,
--     estimated_revenue_opportunity
-- FROM vw_cross_sell
-- WHERE customer_value_tier IN ('Gold', 'Platinum')
--   AND estimated_revenue_opportunity > 200
-- ORDER BY estimated_revenue_opportunity DESC;

-- =============================================================================
-- STORED PROCEDURES FOR COMMON ANALYTICS
-- =============================================================================

-- Get Customer Summary
CREATE OR ALTER PROCEDURE sp_GetCustomerSummary
    @customer_id VARCHAR(50)
AS
BEGIN
    SELECT
        c.*,
        r.total_risk_score,
        r.risk_category,
        cs.recommendation,
        cs.estimated_revenue_opportunity
    FROM vw_customer_360 c
    LEFT JOIN vw_risk_scoring r ON c.customer_id = r.customer_id
    LEFT JOIN vw_cross_sell cs ON c.customer_id = cs.customer_id
    WHERE c.customer_id = @customer_id;
END;
GO

-- Get Claims for Date Range
CREATE OR ALTER PROCEDURE sp_GetClaimsByDateRange
    @start_date DATE,
    @end_date DATE
AS
BEGIN
    SELECT
        service_date,
        claim_type,
        claim_category,
        species,
        claim_amount,
        paid_amount,
        status,
        provider_name,
        is_in_network
    FROM vw_claims_analytics
    WHERE service_date BETWEEN @start_date AND @end_date
    ORDER BY service_date DESC;
END;
GO

-- =============================================================================
-- END OF SYNAPSE SETUP
-- =============================================================================
