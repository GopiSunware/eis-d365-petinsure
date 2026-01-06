#!/bin/bash
# PetInsure360 - Databricks Notebook Deployment Script
# Deploys Bronze→Silver→Gold ETL notebooks to Azure Databricks
#
# Prerequisites:
# 1. Azure CLI installed and logged in
# 2. Databricks CLI installed: pip install databricks-cli
# 3. Databricks workspace access configured
#
# Author: Sunware Technologies

set -e

# Configuration
RESOURCE_GROUP="rg-petinsure360"
DATABRICKS_WORKSPACE="petinsure360-databricks-dev"
NOTEBOOKS_DIR="$(dirname "$0")"
TARGET_PATH="/Shared/PetInsure360"

echo "================================================"
echo "PetInsure360 - Databricks Notebook Deployment"
echo "================================================"

# Get Databricks workspace URL
echo "Getting Databricks workspace info..."
WORKSPACE_URL=$(az databricks workspace show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DATABRICKS_WORKSPACE" \
    --query "workspaceUrl" -o tsv)

if [ -z "$WORKSPACE_URL" ]; then
    echo "ERROR: Could not find Databricks workspace"
    exit 1
fi

echo "Workspace URL: https://$WORKSPACE_URL"

# Configure Databricks CLI with AAD token
echo ""
echo "Configuring Databricks CLI..."
export DATABRICKS_HOST="https://$WORKSPACE_URL"

# Get AAD token for Databricks
DATABRICKS_TOKEN=$(az account get-access-token \
    --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d \
    --query accessToken -o tsv)

if [ -z "$DATABRICKS_TOKEN" ]; then
    echo "ERROR: Could not get Azure AD token for Databricks"
    exit 1
fi

export DATABRICKS_TOKEN

# Create target directory in workspace
echo ""
echo "Creating workspace directory: $TARGET_PATH"
databricks workspace mkdirs "$TARGET_PATH" 2>/dev/null || true

# Deploy notebooks
echo ""
echo "Deploying notebooks..."

for notebook in "01_bronze_ingestion" "02_silver_transformations" "03_gold_aggregations"; do
    source_file="$NOTEBOOKS_DIR/${notebook}.py"
    target_file="$TARGET_PATH/$notebook"

    if [ -f "$source_file" ]; then
        echo "  Uploading: $notebook.py -> $target_file"
        databricks workspace import "$source_file" "$target_file" \
            --language PYTHON \
            --overwrite
    else
        echo "  WARNING: $source_file not found"
    fi
done

# Deploy SQL script
if [ -f "$NOTEBOOKS_DIR/synapse_gold_views.sql" ]; then
    echo "  Uploading: synapse_gold_views.sql -> $TARGET_PATH/synapse_gold_views"
    databricks workspace import "$NOTEBOOKS_DIR/synapse_gold_views.sql" "$TARGET_PATH/synapse_gold_views" \
        --language SQL \
        --overwrite
fi

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Notebooks deployed to: $TARGET_PATH"
echo ""
echo "Next steps:"
echo "1. Open Databricks workspace: https://$WORKSPACE_URL"
echo "2. Navigate to Workspace → Shared → PetInsure360"
echo "3. Create a cluster if not exists"
echo "4. Run notebooks in order:"
echo "   - 01_bronze_ingestion"
echo "   - 02_silver_transformations"
echo "   - 03_gold_aggregations"
echo ""
echo "For full ETL, use Databricks Workflows to orchestrate."
