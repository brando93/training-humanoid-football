# AMI de entrenamiento: Deep Learning Base (driver NVIDIA + Docker) + Isaac Lab fijado + ProtoMotions + MuJoCo.
#
# Se construye en una instancia CPU spot barata (~$0,13/h): no hace falta GPU para instalar.
# Conexión por SSM Session Manager: la instancia de build no abre ningún puerto de entrada.
#
# Uso:  make ami          (desde la raíz del repo)
# Costo: build ~$0,20; snapshot de la AMI ~$3/mes (se conserva solo la más reciente).

packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = ">= 1.3.0"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "subnet_id" {
  description = "Subred pública del stack base (us-east-1a)."
  type        = string
  default     = "subnet-0481604e496f70b73"
}

variable "security_group_id" {
  description = "SG humanoid-trainer: sin entrada, solo salida."
  type        = string
  default     = "sg-0f70aac02b253aa4c"
}

variable "isaaclab_commit" {
  description = "Commit de Isaac Lab fijado por la documentación de ProtoMotions (Isaac Sim 6.0)."
  type        = string
  default     = "4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8"
}

variable "protomotions_commit" {
  description = "Commit de ProtoMotions (main del 2026-11-10: Anatomical SOMA GPC prior)."
  type        = string
  default     = "13de0cccd06f53ce5c9cf9ec7d1932c7da73610f"
}

locals {
  stamp = formatdate("YYYYMMDD-hhmm", timestamp())
}

source "amazon-ebs" "trainer" {
  region          = var.region
  profile         = "humanoid"
  ami_name        = "humanoid-trainer-${local.stamp}"
  ami_description = "Isaac Lab ${substr(var.isaaclab_commit, 0, 8)} + ProtoMotions ${substr(var.protomotions_commit, 0, 8)} + MuJoCo"

  source_ami_filter {
    filters = {
      name                = "Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04) *"
      architecture        = "x86_64"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    owners      = ["amazon"]
    most_recent = true
  }

  # Build en CPU spot: elige el tipo más barato disponible.
  spot_instance_types = ["m7i.2xlarge", "m6i.2xlarge", "m7i-flex.2xlarge", "c7i.2xlarge"]
  spot_price          = "auto"

  subnet_id                   = var.subnet_id
  security_group_id           = var.security_group_id
  associate_public_ip_address = true
  iam_instance_profile        = "humanoid-trainer"

  communicator  = "ssh"
  ssh_username  = "ubuntu"
  ssh_interface = "session_manager"
  ssh_timeout   = "20m"

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 150
    volume_type           = "gp3"
    delete_on_termination = true
  }

  run_tags = {
    Project = "humanoid"
    Name    = "humanoid-packer-build"
  }
  tags = {
    Project            = "humanoid"
    ManagedBy          = "packer"
    IsaacLabCommit     = var.isaaclab_commit
    ProtoMotionsCommit = var.protomotions_commit
  }
  snapshot_tags = {
    Project = "humanoid"
  }
}

build {
  sources = ["source.amazon-ebs.trainer"]

  provisioner "shell" {
    environment_vars = [
      "ISAACLAB_COMMIT=${var.isaaclab_commit}",
      "PROTOMOTIONS_COMMIT=${var.protomotions_commit}",
    ]
    script          = "${path.root}/scripts/provision.sh"
    execute_command = "chmod +x {{ .Path }}; sudo env {{ .Vars }} bash '{{ .Path }}'"
    timeout         = "2h"
  }

  post-processor "manifest" {
    output     = "${path.root}/manifest.json"
    strip_path = true
  }
}
