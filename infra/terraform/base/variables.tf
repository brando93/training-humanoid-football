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

# El repo usa subjects OIDC inmutables: el claim `sub` incluye los IDs numéricos
# del dueño y del repo, así que un repo renombrado o recreado con el mismo nombre no coincide.
# Ver: gh api repos/brando93/training-humanoid-football/actions/oidc/customization/sub
variable "github_sub_prefix" {
  description = "Prefijo del claim sub de los tokens OIDC de este repo."
  type        = string
  default     = "repo:brando93@45773752/training-humanoid-football@1467320856"
}
