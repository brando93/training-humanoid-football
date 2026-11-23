# Launch template de la instancia GPU de entrenamiento (etapa I4).
# Costo fijo: $0. Solo se paga mientras una instancia lanzada con ella está corriendo
# (spot ~$0,23/h g4dn.2xlarge, ~$0,70/h g6.2xlarge) más su disco gp3 (~$0,016/h por 150 GB).
#
# Seguros contra gasto:
#   - spot de una sola vez, se TERMINA (no se detiene) si AWS la reclama;
#   - apagar desde dentro = terminar (instance_initiated_shutdown_behavior);
#   - user data programa un apagado forzado a los `max_runtime_minutes` del arranque;
#   - el disco se borra al terminar.
# El tipo de instancia se elige al lanzar (no está fijado aquí).

variable "max_runtime_minutes" {
  description = "Apagado forzado (y por tanto terminación) de cada instancia tras este tiempo."
  type        = number
  default     = 90
}

# La AMI privada más reciente construida con Packer (infra/packer). Nunca se comparte.
data "aws_ami" "trainer" {
  owners      = ["self"]
  most_recent = true
  filter {
    name   = "name"
    values = ["humanoid-trainer-*"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_launch_template" "trainer" {
  name                                 = "humanoid-trainer"
  description                          = "GPU spot de entrenamiento: sin entrada, SSM, apagado forzado"
  image_id                             = data.aws_ami.trainer.id
  instance_initiated_shutdown_behavior = "terminate"
  update_default_version               = true
  ebs_optimized                        = true

  iam_instance_profile {
    name = aws_iam_instance_profile.trainer.name
  }

  network_interfaces {
    associate_public_ip_address = true # sale a internet por el IGW (sin NAT); no acepta entradas
    security_groups             = [aws_security_group.trainer.id]
    delete_on_termination       = true
  }

  instance_market_options {
    market_type = "spot"
    spot_options {
      spot_instance_type             = "one-time"
      instance_interruption_behavior = "terminate"
    }
  }

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size           = 150
      volume_type           = "gp3"
      delete_on_termination = true
      encrypted             = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2
    http_put_response_hop_limit = 2
  }

  monitoring {
    enabled = false # el monitoreo detallado cobra
  }

  user_data = base64encode(<<-EOT
    #!/bin/bash
    # Seguro de costo: apagado forzado; con shutdown_behavior=terminate la instancia se borra.
    shutdown -h +${var.max_runtime_minutes} "humanoid: tiempo máximo alcanzado"
  EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags          = { Name = "humanoid-trainer", Project = "humanoid" }
  }

  tag_specifications {
    resource_type = "volume"
    tags          = { Name = "humanoid-trainer", Project = "humanoid" }
  }

  tag_specifications {
    resource_type = "spot-instances-request"
    tags          = { Name = "humanoid-trainer", Project = "humanoid" }
  }
}

output "trainer_launch_template_id" {
  value = aws_launch_template.trainer.id
}

output "trainer_ami_id" {
  value = data.aws_ami.trainer.id
}
