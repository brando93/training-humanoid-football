# Roles de GitHub Actions para el ciclo diario de entrenamiento y review. Ambos confían SOLO en workflows
# de la rama main (mismo trust que publish-code: data.aws_iam_policy_document.gha_main_trust). IAM es gratis.
#
#   humanoid-gha-launcher : lanza UNA instancia GPU con el launch template (corrida diaria).
#   humanoid-gha-runs     : lee reportes/videos de las corridas (para abrir el PR) y promueve el modelo
#                           aprobado (copia candidates/<run> -> approved/ cuando Brandon hace merge).

# ---------------------------------------------------------------------------
# Lanzador
# ---------------------------------------------------------------------------
resource "aws_iam_role" "gha_launcher" {
  name                 = "humanoid-gha-launcher"
  description          = "GitHub Actions: lanza la corrida GPU diaria con el launch template"
  assume_role_policy   = data.aws_iam_policy_document.gha_main_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "gha_launcher" {
  statement {
    sid = "Describe"
    actions = [
      "ec2:DescribeInstances", "ec2:DescribeSubnets", "ec2:DescribeSecurityGroups",
      "ec2:DescribeSpotPriceHistory", "ec2:DescribeLaunchTemplates", "ec2:DescribeLaunchTemplateVersions",
      "ec2:DescribeImages",
    ]
    resources = ["*"]
  }

  # Solo puede lanzar con NUESTRO launch template (que fija AMI, spot, disco, apagado forzado) y tipos GPU.
  statement {
    sid       = "RunWithTemplateOnly"
    actions   = ["ec2:RunInstances"]
    resources = ["arn:aws:ec2:${var.region}:${var.account_id}:instance/*"]
    condition {
      test     = "ArnLike"
      variable = "ec2:LaunchTemplate"
      values   = [aws_launch_template.trainer.arn]
    }
    condition {
      test     = "StringLike"
      variable = "ec2:InstanceType"
      values   = ["g6.2xlarge", "g6.xlarge", "g4dn.2xlarge", "g4dn.xlarge"]
    }
  }

  statement {
    sid     = "RunSupportingResources"
    actions = ["ec2:RunInstances"]
    resources = [
      "arn:aws:ec2:${var.region}:${var.account_id}:network-interface/*",
      "arn:aws:ec2:${var.region}:${var.account_id}:volume/*",
      "arn:aws:ec2:${var.region}:${var.account_id}:subnet/*",
      "arn:aws:ec2:${var.region}:${var.account_id}:security-group/*",
      "arn:aws:ec2:${var.region}:${var.account_id}:launch-template/*",
      "arn:aws:ec2:${var.region}:${var.account_id}:spot-instances-request/*",
      "arn:aws:ec2:${var.region}::image/*",
    ]
  }

  statement {
    sid       = "TagOnLaunch"
    actions   = ["ec2:CreateTags"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "ec2:CreateAction"
      values   = ["RunInstances"]
    }
  }

  statement {
    sid       = "PassTrainerRole"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.trainer.arn]
  }

  statement {
    sid       = "SpotServiceLinkedRole"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = ["arn:aws:iam::${var.account_id}:role/aws-service-role/spot.amazonaws.com/*"]
  }

  # El lanzador respeta el freno de costos y muestra el gasto.
  statement {
    sid       = "ReadGuard"
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/humanoid/guard/*"]
  }

  statement {
    sid       = "ReadLedger"
    actions   = ["s3:GetObject"]
    resources = ["${local.artifacts_arn}/guard/*"]
  }
}

resource "aws_iam_role_policy" "gha_launcher" {
  name   = "launch-trainer"
  role   = aws_iam_role.gha_launcher.id
  policy = data.aws_iam_policy_document.gha_launcher.json
}

# ---------------------------------------------------------------------------
# Reportes y promoción del modelo aprobado
# ---------------------------------------------------------------------------
resource "aws_iam_role" "gha_runs" {
  name                 = "humanoid-gha-runs"
  description          = "GitHub Actions: lee reportes de corridas y promueve el modelo aprobado"
  assume_role_policy   = data.aws_iam_policy_document.gha_main_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "gha_runs" {
  statement {
    sid       = "List"
    actions   = ["s3:ListBucket"]
    resources = [local.artifacts_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["reports/runs/*", "checkpoints/3b/*", "guard/*"]
    }
  }

  statement {
    sid       = "ReadRunsAndCandidates"
    actions   = ["s3:GetObject"]
    resources = ["${local.artifacts_arn}/reports/runs/*", "${local.artifacts_arn}/checkpoints/3b/candidates/*", "${local.artifacts_arn}/guard/*"]
  }

  statement {
    sid       = "PromoteApproved"
    actions   = ["s3:PutObject", "s3:DeleteObject"]
    resources = ["${local.artifacts_arn}/checkpoints/3b/approved/*", "${local.artifacts_arn}/checkpoints/3b/approved.json"]
  }
}

resource "aws_iam_role_policy" "gha_runs" {
  name   = "runs"
  role   = aws_iam_role.gha_runs.id
  policy = data.aws_iam_policy_document.gha_runs.json
}

output "gha_launcher_role_arn" {
  value = aws_iam_role.gha_launcher.arn
}

output "gha_runs_role_arn" {
  value = aws_iam_role.gha_runs.arn
}
