#!/bin/bash
set -e

echo "Starting provisioning..."

# Install Docker only if missing
if ! command -v docker &> /dev/null
then
    echo "Installing Docker..."
    sudo apt update -y
    sudo apt install -y docker.io docker-compose-plugin
fi

# Start Docker if inactive
sudo systemctl enable docker
sudo systemctl start docker

# Create backup directory if missing
mkdir -p /tmp/cyberoracle-backups

# Launch services only if not already running
if [ "$(docker ps -q -f name=cyberoracle-api)" ]; then
    echo "CyberOracle stack already running."
else
    echo "Starting CyberOracle stack..."
    docker compose up -d --build
fi

echo "Current containers:"
docker ps