from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import AppRunner
from diagrams.aws.storage import S3
from diagrams.azure.analytics import Databricks
from diagrams.azure.storage import DataLakeStorage
from diagrams.azure.security import KeyVaults
from diagrams.saas.chat import Slack
from diagrams.onprem.client import User
from diagrams.custom import Custom

# Ensure you have graphviz installed: https://graphviz.org/download/
# pip install diagrams

with Diagram("Hybrid Cloud Architecture", show=False, direction="LR"):
    user = User("Customer")

    with Cluster("AWS Cloud (Compute Layer)"):
        with Cluster("Frontends"):
            portal = S3("Customer Portal")
            dashboard = S3("BI Dashboard")
            agent_ui = S3("Agent Portal")

        with Cluster("Backend Services"):
            api = AppRunner("Claims Data API")
            pipeline = AppRunner("Agent Pipeline")
            docgen = AppRunner("DocGen AI")

        user >> portal
        portal >> api
        dashboard >> api
        agent_ui >> api
        
        api >> pipeline
        pipeline >> docgen

    with Cluster("Azure Cloud (Data Platform)"):
        with Cluster("Storage"):
            adls = DataLakeStorage("ADLS Gen2\n(Raw/Bronze/Silver/Gold)")
        
        with Cluster("Analytics"):
            db = Databricks("Databricks ETL")
            kv = KeyVaults("Key Vault")

        api >> Edge(label="Read Gold Data", color="orange") >> adls
        api >> Edge(label="Write Raw Data", color="blue") >> adls
        
        db >> Edge(label="Medallion Processing") >> adls

with Diagram("Insurance Claim Lifecycle", show=False, direction="LR"):
    start = User("User Upload")
    
    with Cluster("Processing Pipeline"):
        ai = AppRunner("AI DocGen")
        valid = AppRunner("Validation")
        risk = Databricks("Risk Scoring")
        approve = Slack("Approval Notification")
        
        start >> Edge(label="1. Submit") >> ai
        ai >> Edge(label="2. Extract") >> valid
        valid >> Edge(label="3. Risk Check") >> risk
        risk >> Edge(label="4. Decision") >> approve

print("Diagrams generated successfully: 'hybrid_cloud_architecture.png' and 'insurance_claim_lifecycle.png'")
