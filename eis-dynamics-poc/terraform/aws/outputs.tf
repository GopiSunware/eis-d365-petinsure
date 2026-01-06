# Outputs for EIS-Dynamics AWS Infrastructure

output "ecr_unified_api_url" {
  description = "ECR repository URL for Unified API"
  value       = aws_ecr_repository.unified_api.repository_url
}

output "ecr_agent_pipeline_url" {
  description = "ECR repository URL for Agent Pipeline"
  value       = aws_ecr_repository.agent_pipeline.repository_url
}

output "unified_api_url" {
  description = "App Runner URL for Unified Claims API"
  value       = "https://${aws_apprunner_service.unified_api.service_url}"
}

output "agent_pipeline_url" {
  description = "App Runner URL for Agent Pipeline"
  value       = "https://${aws_apprunner_service.agent_pipeline.service_url}"
}

output "frontend_bucket" {
  description = "S3 bucket for frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "datalake_bucket" {
  description = "S3 bucket for Data Lake (raw/bronze/silver/gold)"
  value       = aws_s3_bucket.datalake.bucket
}

output "datalake_bucket_arn" {
  description = "S3 bucket ARN for Data Lake"
  value       = aws_s3_bucket.datalake.arn
}

output "frontend_website_url" {
  description = "S3 website URL for frontend"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}
