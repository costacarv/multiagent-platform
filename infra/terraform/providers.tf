terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  backend "s3" {
  bucket         = "tfstate-multiagent-617087574557"
  key            = "eks/terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "terraform-state-lock"
  encrypt        = true
}

}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "multiagent-due-diligence"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}