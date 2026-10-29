terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# Default region for the primary bucket
provider "aws" {
  region = "us-east-1"
}

# A different region is required for cross-region replication
provider "aws" {
  alias  = "replica"
  region = "us-east-2"
}

data "aws_caller_identity" "current" {}

# --------------------------------------------------
# KMS key for the primary bucket
# --------------------------------------------------

resource "aws_kms_key" "s3_key" {
  description             = "KMS key for DevSecOps demo S3 bucket"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid    = "EnableAccountIAMPermissions"
      Effect = "Allow"

      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }

      Action   = "kms:*"
      Resource = "*"
    }]
  })
}

resource "aws_kms_key" "logs_key" {
  description             = "KMS key for access-logs bucket"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "EnableAccountIAMPermissions"
      Effect = "Allow"

      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }

      Action   = "kms:*"
      Resource = "*"
    }]
  })
}
# --------------------------------------------------
# Primary S3 bucket
# --------------------------------------------------

resource "aws_s3_bucket" "project_bucket" {
  bucket = "cybersecurity-project-demo-unique-12345"

  tags = {
    Project = "Agentic-DevSecOps"
    Purpose = "Security-Testing"
  }
}

resource "aws_s3_bucket_public_access_block" "project_bucket" {
  bucket                  = aws_s3_bucket.project_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "project_bucket" {
  bucket = aws_s3_bucket.project_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "project_bucket" {
  bucket = aws_s3_bucket.project_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_key.arn
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "project_bucket" {
  bucket = aws_s3_bucket.project_bucket.id

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# --------------------------------------------------
# Access logging destination bucket
# Supporting bucket: recursive policies are documented
# as out of scope for this static-analysis demo.
# --------------------------------------------------

resource "aws_s3_bucket" "access_logs" {
  bucket = "cybersecurity-project-logs-demo-unique-12345"

  # checkov:skip=CKV_AWS_18:Logging destination bucket for this demo
  # checkov:skip=CKV_AWS_144:Supporting logging bucket is not replicated
  # checkov:skip=CKV2_AWS_62:Supporting logging bucket has no event consumer
}

resource "aws_s3_bucket_versioning" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket                  = aws_s3_bucket.access_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.logs_key.arn
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_logging" "project_bucket" {
  bucket        = aws_s3_bucket.project_bucket.id
  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "s3-access-logs/"
}

# --------------------------------------------------
# S3 event notifications using SQS
# --------------------------------------------------

resource "aws_sqs_queue" "s3_events" {
  name                    = "cybersecurity-project-s3-events"
  sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue_policy" "s3_events" {
  queue_url = aws_sqs_queue.s3_events.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid    = "AllowS3ToSendMessages"
      Effect = "Allow"

      Principal = {
        Service = "s3.amazonaws.com"
      }

      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.s3_events.arn

      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_s3_bucket.project_bucket.arn
        }

        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "project_bucket" {
  bucket = aws_s3_bucket.project_bucket.id

  queue {
    queue_arn = aws_sqs_queue.s3_events.arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_sqs_queue_policy.s3_events]
}

# --------------------------------------------------
# Cross-region replication destination
# --------------------------------------------------

resource "aws_s3_bucket" "replica" {
  provider = aws.replica
  bucket   = "cybersecurity-project-replica-demo-unique-12345"

  # checkov:skip=CKV_AWS_18:Replica bucket logging is outside demo scope
  # checkov:skip=CKV_AWS_144:Replication destination is not recursively replicated
  # checkov:skip=CKV2_AWS_62:Replica bucket event processing is outside demo scope
}

resource "aws_s3_bucket_public_access_block" "replica" {
  provider                = aws.replica
  bucket                  = aws_s3_bucket.replica.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica.id

  rule {
    id     = "manage-replica-objects"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    id     = "manage-access-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_kms_key" "replica_key" {
  provider                = aws.replica
  description             = "KMS key for replica bucket"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid    = "EnableAccountIAMPermissions"
      Effect = "Allow"

      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }

      Action   = "kms:*"
      Resource = "*"
    }]
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "replica" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.replica_key.arn
    }

    bucket_key_enabled = true
  }
}

# --------------------------------------------------
# IAM role and permissions for replication
# --------------------------------------------------

resource "aws_iam_role" "replication" {
  name = "cybersecurity-project-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "s3.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "replication" {
  name = "cybersecurity-project-replication-policy"
  role = aws_iam_role.replication.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]

        Resource = [aws_s3_bucket.project_bucket.arn]
      },
      {
        Effect = "Allow"

        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]

        Resource = ["${aws_s3_bucket.project_bucket.arn}/*"]
      },
      {
        Effect = "Allow"

        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]

        Resource = ["${aws_s3_bucket.replica.arn}/*"]
      },
      {
        Effect = "Allow"

        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]

        Resource = [aws_kms_key.s3_key.arn]
      },
      {
        Effect = "Allow"

        Action = [
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]

        Resource = [aws_kms_key.replica_key.arn]
      }
    ]
  })
}

resource "aws_s3_bucket_replication_configuration" "project_bucket" {
  bucket = aws_s3_bucket.project_bucket.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-all-objects"
    status = "Enabled"

    filter {}

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }

    destination {
      bucket = aws_s3_bucket.replica.arn

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.replica_key.arn
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.project_bucket,
    aws_s3_bucket_versioning.replica,
    aws_iam_role_policy.replication
  ]
}
