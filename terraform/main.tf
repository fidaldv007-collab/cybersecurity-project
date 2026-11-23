terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

#checkov:skip=CKV_AWS_144:Cross-region replication not required for demo environment
#checkov:skip=CKV2_AWS_62:Event notifications handled externally
resource "aws_s3_bucket" "security_reports" {
  bucket = "cnapp-security-reports-archive"
}

resource "aws_s3_bucket_public_access_block" "security_reports_pab" {
  bucket                  = aws_s3_bucket.security_reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "security_reports_versioning" {
  bucket = aws_s3_bucket.security_reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "security_reports_sse" {
  bucket = aws_s3_bucket.security_reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
