# Stack base: identidad de GitHub Actions en AWS (OIDC).
# Más adelante aquí se agregan VPC, buckets de datos, launch template, etc.
# Costo actual de este stack: $0 (IAM y OIDC son gratis).

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    bucket       = "humanoid-tfstate-611606529792"
    key          = "base/terraform.tfstate"
    region       = "us-east-1"
    profile      = "humanoid"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region              = var.region
  profile             = "humanoid"
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      Project   = "humanoid"
      ManagedBy = "terraform"
      Stack     = "base"
    }
  }
}
