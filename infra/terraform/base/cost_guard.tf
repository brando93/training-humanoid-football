# Freno de costos (infra/guard/cost_guard.py): Lambda cada 10 min que termina las GPU y bloquea
# lanzamientos si una corrida pasa de 100 min, la GPU del día pasa de $3 o la factura del mes llega a $45.
#
# Costo: ~$0. 4.320 invocaciones/mes de ~2 s con 128 MB = ~1.100 GB-s (nivel gratuito: 400.000 GB-s y
# 1M de invocaciones, permanente). EventBridge Scheduler: 14M invocaciones gratis/mes. Logs: KB/día,
# retención 7 días. Lecturas de Budgets (describe_budget): gratis. Llamadas S3/SSM: centavos al año.

variable "guard_max_run_min" {
  type    = number
  default = 100
}

variable "guard_daily_cap_usd" {
  type    = number
  default = 3
}

variable "guard_month_stop_usd" {
  type    = number
  default = 45
}

data "archive_file" "cost_guard" {
  type        = "zip"
  source_file = "${path.module}/../../guard/cost_guard.py"
  output_path = "${path.module}/.build/cost_guard.zip"
}

resource "aws_cloudwatch_log_group" "cost_guard" {
  name              = "/aws/lambda/humanoid-cost-guard"
  retention_in_days = 7
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cost_guard" {
  name               = "humanoid-cost-guard"
  description        = "Freno de costos: termina GPU y bloquea lanzamientos"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "cost_guard" {
  statement {
    sid       = "Describe"
    actions   = ["ec2:DescribeInstances", "ec2:DescribeSpotPriceHistory"]
    resources = ["*"]
  }

  # Solo puede terminar instancias GPU (g*, p*) o las del proyecto.
  statement {
    sid       = "TerminateGpu"
    actions   = ["ec2:TerminateInstances"]
    resources = ["arn:aws:ec2:${var.region}:${var.account_id}:instance/*"]
    condition {
      test     = "StringLike"
      variable = "ec2:InstanceType"
      values   = ["g*", "p*"]
    }
  }

  statement {
    sid       = "TerminateTrainer"
    actions   = ["ec2:TerminateInstances"]
    resources = ["arn:aws:ec2:${var.region}:${var.account_id}:instance/*"]
    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/Name"
      values   = ["humanoid-trainer"]
    }
  }

  statement {
    sid       = "Ledger"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${local.artifacts_arn}/guard/*"]
  }

  statement {
    sid       = "LedgerList" # sin ListBucket, un objeto inexistente da 403 en vez de NoSuchKey
    actions   = ["s3:ListBucket"]
    resources = [local.artifacts_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["guard/*"]
    }
  }

  statement {
    sid       = "BlockFlag"
    actions   = ["ssm:GetParameter", "ssm:PutParameter", "ssm:DeleteParameter"]
    resources = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/humanoid/guard/*"]
  }

  statement {
    sid       = "ReadBudget"
    actions   = ["budgets:ViewBudget"]
    resources = ["arn:aws:budgets::${var.account_id}:budget/humanoid-monthly-50"]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.cost_guard.arn}:*"]
  }
}

resource "aws_iam_role_policy" "cost_guard" {
  name   = "cost-guard"
  role   = aws_iam_role.cost_guard.id
  policy = data.aws_iam_policy_document.cost_guard.json
}

resource "aws_lambda_function" "cost_guard" {
  function_name    = "humanoid-cost-guard"
  description      = "Freno de costos: GPU > ${var.guard_max_run_min} min, > $${var.guard_daily_cap_usd}/día o factura >= $${var.guard_month_stop_usd}"
  role             = aws_iam_role.cost_guard.arn
  runtime          = "python3.12"
  handler          = "cost_guard.handler"
  filename         = data.archive_file.cost_guard.output_path
  source_code_hash = data.archive_file.cost_guard.output_base64sha256
  memory_size      = 128
  timeout          = 60
  architectures    = ["arm64"]

  environment {
    variables = {
      BUCKET         = aws_s3_bucket.artifacts.id
      ACCOUNT_ID     = var.account_id
      BUDGET_NAME    = "humanoid-monthly-50"
      MAX_RUN_MIN    = tostring(var.guard_max_run_min)
      DAILY_CAP_USD  = tostring(var.guard_daily_cap_usd)
      MONTH_STOP_USD = tostring(var.guard_month_stop_usd)
    }
  }

  depends_on = [aws_cloudwatch_log_group.cost_guard, aws_iam_role_policy.cost_guard]
}

data "aws_iam_policy_document" "scheduler_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cost_guard_scheduler" {
  name               = "humanoid-cost-guard-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_trust.json
}

resource "aws_iam_role_policy" "cost_guard_scheduler" {
  name = "invoke-cost-guard"
  role = aws_iam_role.cost_guard_scheduler.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "lambda:InvokeFunction", Resource = aws_lambda_function.cost_guard.arn }]
  })
}

resource "aws_scheduler_schedule" "cost_guard" {
  name                = "humanoid-cost-guard"
  schedule_expression = "rate(10 minutes)"
  flexible_time_window {
    mode = "OFF"
  }
  target {
    arn      = aws_lambda_function.cost_guard.arn
    role_arn = aws_iam_role.cost_guard_scheduler.arn
    retry_policy {
      maximum_retry_attempts = 1
    }
  }
}

output "cost_guard_function" {
  value = aws_lambda_function.cost_guard.function_name
}
