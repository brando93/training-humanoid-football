variable "account_id" {
  description = "Cuenta AWS personal del proyecto. El provider se niega a operar en otra."
  type        = string
  default     = "611606529792"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "github_repo" {
  description = "Repositorio (owner/name) en el que confían los roles OIDC."
  type        = string
  default     = "brando93/training-humanoid-football"
}
