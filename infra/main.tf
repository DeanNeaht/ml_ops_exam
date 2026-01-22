terraform {
  required_version = ">= 1.0.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "docker" {}
provider "local" {}
provider "null" {}

resource "local_file" "bucket_config" {
  filename = "${var.bucket_path}/.bucket-config.json"
  content = jsonencode({
    bucket_name = var.bucket_name
    created_at  = timestamp()
    versioning  = var.bucket_versioning
    tags        = var.common_tags
  })
}

resource "null_resource" "create_bucket_structure" {
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p ${var.bucket_path}/models
      mkdir -p ${var.bucket_path}/data
      mkdir -p ${var.bucket_path}/artifacts
      mkdir -p ${var.bucket_path}/logs
    EOT
  }

  triggers = {
    bucket_name = var.bucket_name
  }

  depends_on = [local_file.bucket_config]
}

resource "docker_network" "mlops_network" {
  name   = var.docker_network_name
  driver = "bridge"

  labels {
    label = "project"
    value = "mlops"
  }
}

resource "docker_image" "python" {
  name         = "python:3.11-slim"
  keep_locally = true
}

resource "null_resource" "build_ml_service" {
  provisioner "local-exec" {
    command     = "docker build -t ${var.ml_service_image}:${var.model_version} ."
    working_dir = var.project_root
    on_failure  = continue
  }

  triggers = {
    dockerfile_hash = filemd5("${var.project_root}/Dockerfile")
    version         = var.model_version
  }
}

resource "docker_image" "prometheus" {
  name         = "prom/prometheus:v2.47.0"
  keep_locally = true
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:10.2.0"
  keep_locally = true
}

resource "local_file" "env_config" {
  filename = "${var.project_root}/.env.terraform"
  content  = <<-EOT
    MODEL_VERSION=${var.model_version}
    MODEL_PATH=${var.bucket_path}/models/model.pkl
    BUCKET_PATH=${var.bucket_path}
    MLFLOW_TRACKING_URI=${var.mlflow_tracking_uri}
    MLFLOW_EXPERIMENT_NAME=${var.mlflow_experiment_name}
    SERVICE_HOST=${var.service_host}
    SERVICE_PORT=${var.service_port}
    PROMETHEUS_PORT=${var.prometheus_port}
    GRAFANA_PORT=${var.grafana_port}
  EOT

  file_permission = "0644"
}

resource "local_file" "deployment_info" {
  filename = "${var.project_root}/deployment-info.json"
  content = jsonencode({
    project         = "mlops-exam"
    environment     = var.environment
    model_version   = var.model_version
    bucket_path     = var.bucket_path
    network_name    = docker_network.mlops_network.name
    service_port    = var.service_port
    prometheus_port = var.prometheus_port
    grafana_port    = var.grafana_port
    deployed_at     = timestamp()
  })

  file_permission = "0644"
}
