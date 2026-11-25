# Red mínima y gratis: VPC con subredes públicas, SIN NAT Gateway (ahorra ~$33/mes).
# La instancia GPU sale a internet por el Internet Gateway con una IP pública temporal
# (solo cobra mientras la instancia corre) y no acepta ninguna conexión entrante.
# Costo fijo de todo este archivo: $0.

locals {
  # Varias zonas = más pools de capacidad spot donde buscar GPU.
  # us-east-1f (2026-11-25): la g6.2xlarge spot suele ser la más barata ahí (~$0,70 vs ~$0,82). us-east-1e no ofrece g6.
  azs = ["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d", "us-east-1f"]
}

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "humanoid" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "humanoid" }
}

resource "aws_subnet" "public" {
  for_each                = { for i, az in local.azs : az => i }
  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.key
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, each.value)
  map_public_ip_on_launch = true
  tags                    = { Name = "humanoid-public-${each.key}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "humanoid-public" }
}

resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# Endpoint gateway de S3: el tráfico a S3 no pasa por internet. Es gratis
# (los endpoints "interface" sí cobran ~$7/mes cada uno; no usamos ninguno).
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id]
  tags              = { Name = "humanoid-s3" }
}

# El security group por defecto de la VPC queda sin reglas, para que nada lo use por accidente.
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "humanoid-default-locked" }
}

# Security group de la instancia de entrenamiento: CERO puertos de entrada (sin SSH).
# Se entra con SSM Session Manager, que funciona por conexión saliente.
resource "aws_security_group" "trainer" {
  name        = "humanoid-trainer"
  description = "Instancia GPU: sin entrada, salida HTTPS/HTTP para S3, SSM, NGC y paquetes"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "humanoid-trainer" }
}

resource "aws_vpc_security_group_egress_rule" "trainer_https" {
  security_group_id = aws_security_group.trainer.id
  description       = "HTTPS saliente"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "trainer_http" {
  security_group_id = aws_security_group.trainer.id
  description       = "HTTP saliente (repositorios de paquetes)"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "trainer_dns" {
  security_group_id = aws_security_group.trainer.id
  description       = "DNS del resolver de la VPC"
  cidr_ipv4         = "${cidrhost(aws_vpc.main.cidr_block, 2)}/32"
  ip_protocol       = "udp"
  from_port         = 53
  to_port           = 53
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [for s in aws_subnet.public : s.id]
}

output "trainer_security_group_id" {
  value = aws_security_group.trainer.id
}
