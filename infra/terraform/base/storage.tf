# Un solo bucket para todos los artefactos del proyecto, separado por prefijos:
#   code/latest.tar.gz        código publicado por GitHub Actions (se sobrescribe en cada merge)
#   code/releases/<sha>.tar.gz historial de código (expira a los 30 días)
#   data/                     mocap con licencia (AMASS, SMPL) y clips propios: no expira
#   checkpoints/latest/       último checkpoint de cada experimento: no expira
#   checkpoints/history/      checkpoints intermedios (expiran a los 14 días)
#   reports/                  reportes diarios: métricas, gráficas, HTML (expiran a los 180 días)
#   reports/videos/           videos demo (expiran a los 45 días)
#   logs/                     logs de las corridas (expiran a los 30 días)
#
# Sin versionado (duplicaría el costo de los checkpoints) y cifrado SSE-S3 (gratis).
# Costo: $0,023 por GB al mes. Con las expiraciones, se espera que quede por debajo de ~30 GB (~$0,70/mes).

resource "aws_s3_bucket" "artifacts" {
  bucket = "humanoid-artifacts-${var.account_id}"
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

locals {
  expirations = {
    "code-releases"       = { prefix = "code/releases/", days = 30 }
    "checkpoints-history" = { prefix = "checkpoints/history/", days = 14 }
    "report-videos"       = { prefix = "reports/videos/", days = 45 }
    "reports"             = { prefix = "reports/", days = 180 }
    "logs"                = { prefix = "logs/", days = 30 }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  dynamic "rule" {
    for_each = local.expirations
    content {
      id     = rule.key
      status = "Enabled"
      filter {
        prefix = rule.value.prefix
      }
      expiration {
        days = rule.value.days
      }
    }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}
