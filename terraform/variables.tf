variable "gateway_replicas" {
  description = "Number of CyberOracle FastAPI gateway replicas to run"
  type        = number
  default     = 2
}

variable "gateway_base_port" {
  description = "Base host port for gateway replicas (replica 0 = base, replica 1 = base+1, ...)"
  type        = number
  default     = 8000
}

variable "postgres_port" {
  description = "Host port mapped to PostgreSQL container"
  type        = number
  default     = 5434
}

variable "jwt_secret" {
  description = "JWT signing secret — set via TF_VAR_jwt_secret env var, never hardcode"
  type        = string
  sensitive   = true
}
