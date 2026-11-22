# GitHub Actions obtiene credenciales temporales de AWS sin ninguna clave guardada.
# Cada rol confía solo en este repo y en una rama o evento concreto.

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Rol de prueba: sin ningún permiso adjunto. Solo sirve para comprobar que OIDC funciona
# (sts:GetCallerIdentity no requiere permisos). Solo lo puede asumir un workflow en main.
data "aws_iam_policy_document" "smoke_trust" {
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

resource "aws_iam_role" "github_smoke" {
  name                 = "humanoid-gha-smoke"
  description          = "Prueba de OIDC desde GitHub Actions. Sin permisos."
  assume_role_policy   = data.aws_iam_policy_document.smoke_trust.json
  max_session_duration = 3600
}

output "github_smoke_role_arn" {
  value = aws_iam_role.github_smoke.arn
}
