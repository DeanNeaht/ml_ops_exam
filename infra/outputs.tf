output "bucket_name" {
  value = var.bucket_name
}

output "bucket_path" {
  value = var.bucket_path
}

output "bucket_structure" {
  value = {
    models    = "${var.bucket_path}/models"
    data      = "${var.bucket_path}/data"
    artifacts = "${var.bucket_path}/artifacts"
    logs      = "${var.bucket_path}/logs"
  }
}

output "docker_network_id" {
  value = docker_network.mlops_network.id
}

output "docker_network_name" {
  value = docker_network.mlops_network.name
}

output "ml_service_url" {
  value = "http://${var.service_host}:${var.service_port}"
}

output "prometheus_url" {
  value = "http://localhost:${var.prometheus_port}"
}

output "grafana_url" {
  value = "http://localhost:${var.grafana_port}"
}

output "service_endpoints" {
  value = {
    ml_service = {
      health  = "http://localhost:${var.service_port}/health"
      predict = "http://localhost:${var.service_port}/predict"
      metrics = "http://localhost:${var.service_port}/metrics"
    }
    monitoring = {
      prometheus = "http://localhost:${var.prometheus_port}"
      grafana    = "http://localhost:${var.grafana_port}"
    }
  }
}

output "model_version" {
  value = var.model_version
}

output "environment" {
  value = var.environment
}
