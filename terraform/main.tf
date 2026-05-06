terraform {
  required_version = ">= 1.3"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ---------------------------------------------------------------------------
# Network — shared bridge so all containers can reach each other by name
# ---------------------------------------------------------------------------
resource "docker_network" "cyberoracle_net" {
  name = "cyberoracle-net"
}

# ---------------------------------------------------------------------------
# PostgreSQL database
# ---------------------------------------------------------------------------
resource "docker_container" "postgres" {
  name  = "cyberoracle-db"
  image = "postgres:16"

  networks_advanced {
    name = docker_network.cyberoracle_net.name
  }

  ports {
    internal = 5432
    external = var.postgres_port
  }

  env = [
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=postgres",
    "POSTGRES_DB=cyberoracle",
  ]

  restart = "unless-stopped"
}

# ---------------------------------------------------------------------------
# FastAPI gateway — scaled to var.gateway_replicas instances
# ---------------------------------------------------------------------------
resource "docker_container" "gateway" {
  count = var.gateway_replicas
  name  = "cyberoracle-api-${count.index}"
  image = "cyberoracle-api:latest"

  networks_advanced {
    name = docker_network.cyberoracle_net.name
  }

  ports {
    internal = 8000
    external = var.gateway_base_port + count.index
  }

  env = [
    "DATABASE_URL=postgresql+asyncpg://postgres:postgres@cyberoracle-db:5432/cyberoracle",
    "DB_ENCRYPTION_ENABLED=true",
    "JWT_SECRET_KEY=${var.jwt_secret}",
  ]

  depends_on = [docker_container.postgres]
  restart    = "unless-stopped"
}
