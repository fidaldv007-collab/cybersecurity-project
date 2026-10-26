terraform {
  required_version = ">= 1.0"
}

resource "aws_s3_bucket" "project_bucket" {
  bucket = "cybersecurity-project-demo-unique-12345"

  tags = {
    Project = "Agentic-DevSecOps"
    Purpose = "Security-Testing"
  }
}



