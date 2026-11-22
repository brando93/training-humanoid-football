# Roles con permisos mínimos. IAM es gratis.

locals {
  artifacts_arn = aws_s3_bucket.artifacts.arn
}

# ---------------------------------------------------------------------------
# Instancia de entrenamiento (EC2 GPU): instance profile, sin claves.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "ec2_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "trainer" {
  name               = "humanoid-trainer"
  description        = "Instancia GPU de entrenamiento"
  assume_role_policy = data.aws_iam_policy_document.ec2_trust.json
}

data "aws_iam_policy_document" "trainer" {
  statement {
    sid       = "ListOwnPrefixes"
    actions   = ["s3:ListBucket"]
    resources = [local.artifacts_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["code/*", "data/*", "checkpoints/*", "reports/*", "logs/*"]
    }
  }

  statement {
    sid       = "ReadCodeAndData"
    actions   = ["s3:GetObject"]
    resources = ["${local.artifacts_arn}/code/*", "${local.artifacts_arn}/data/*"]
  }

  statement {
    sid     = "ReadWriteRunOutputs"
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"]
    resources = [
      "${local.artifacts_arn}/checkpoints/*",
      "${local.artifacts_arn}/reports/*",
      "${local.artifacts_arn}/logs/*",
    ]
  }

  statement {
    sid       = "ReadProjectParameters"
    actions   = ["ssm:GetParameter", "ssm:GetParametersByPath"]
    resources = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/humanoid/*"]
  }
}

resource "aws_iam_role_policy" "trainer" {
  name   = "humanoid-trainer"
  role   = aws_iam_role.trainer.id
  policy = data.aws_iam_policy_document.trainer.json
}

# Session Manager (entrar a la instancia sin SSH ni llaves).
resource "aws_iam_role_policy_attachment" "trainer_ssm" {
  role       = aws_iam_role.trainer.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "trainer" {
  name = "humanoid-trainer"
  role = aws_iam_role.trainer.name
}

# ---------------------------------------------------------------------------
# GitHub Actions: publicar el código en S3 tras cada merge a main.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "gha_main_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${var.github_sub_prefix}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "gha_publish_code" {
  name                 = "humanoid-gha-publish-code"
  description          = "GitHub Actions: sube el código empaquetado a s3://.../code/"
  assume_role_policy   = data.aws_iam_policy_document.gha_main_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "gha_publish_code" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${local.artifacts_arn}/code/*"]
  }
}

resource "aws_iam_role_policy" "gha_publish_code" {
  name   = "publish-code"
  role   = aws_iam_role.gha_publish_code.id
  policy = data.aws_iam_policy_document.gha_publish_code.json
}

output "trainer_instance_profile" {
  value = aws_iam_instance_profile.trainer.name
}

output "gha_publish_code_role_arn" {
  value = aws_iam_role.gha_publish_code.arn
}
