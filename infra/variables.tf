variable "environment" {
  type    = string
  default = "dev"
}

variable "project_root" {
  type    = string
  default = ".."
}

variable "common_tags" {
  type = map(string)
  default = {
    Project     = "mlops-exam"
    ManagedBy   = "terraform"
    Environment = "dev"
  }
}

variable "bucket_name" {
  type    = string
  default = "mlops-artifacts"
}

variable "bucket_path" {
  type    = string
  default = "../storage/mlops-bucket"
}

variable "bucket_versioning" {
  type    = bool
  default = true
}

variable "docker_network_name" {
  type    = string
  default = "mlops-network"
}

variable "ml_service_image" {
  type    = string
  default = "ml-service"
}

variable "model_version" {
  type    = string
  default = "1.0.0"
}

variable "service_host" {
  type    = string
  default = "0.0.0.0"
}

variable "service_port" {
  type    = number
  default = 8000
}

variable "prometheus_port" {
  type    = number
  default = 9090
}

variable "grafana_port" {
  type    = number
  default = 3000
}

variable "mlflow_tracking_uri" {
  type    = string
  default = "./mlruns"
}

variable "mlflow_experiment_name" {
  type    = string
  default = "iris-classification"
}
