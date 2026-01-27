#!/usr/bin/env python3
"""
PSFR8 – Ops Automation Script for Scaling Tasks
==============================================

This script provides a simple operational tool to scale the CyberOracle
gateway service in either:

  - Docker Compose
  - Kubernetes

It is designed to be run manually by operators (or from CI/CD / n8n) to
increase/decrease the number of FastAPI replicas without editing YAML
by hand each time.

Usage examples:

  # Scale Docker Compose service "backend" to 3 replicas
  GATEWAY_SERVICE_NAME=backend python scripts/scale_gateway.py --target docker --replicas 3

  # Scale Kubernetes deployment cyberoracle-gateway to 5 replicas in namespace prod
  K8S_DEPLOYMENT_NAME=cyberoracle-gateway K8S_NAMESPACE=prod \\
      python scripts/scale_gateway.py --target k8s --replicas 5
"""

import argparse
import os
import subprocess
import sys
from typing import Tuple


def run_command(cmd: list[str]) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def scale_docker(replicas: int) -> int:
    """
    Scale the FastAPI gateway when running under Docker Compose.

    Environment variables:
      - GATEWAY_SERVICE_NAME: name of the service in docker-compose.yml
        (e.g. "backend", "api", "fastapi"). Default: "backend".
      - DOCKER_COMPOSE_FILE: path to docker-compose file. Default: "docker-compose.yml"
    """
    service_name = os.getenv("GATEWAY_SERVICE_NAME", "backend")
    compose_file = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml")

    print(
        f"[scale-gateway] Target: Docker Compose | Service={service_name} | "
        f"Replicas={replicas} | File={compose_file}"
    )

    cmd = [
        "docker",
        "compose",
        "-f",
        compose_file,
        "up",
        "-d",
        "--scale",
        f"{service_name}={replicas}",
    ]

    code, out, err = run_command(cmd)

    if code == 0:
        print("[scale-gateway] Docker scaling command completed successfully.")
        if out:
            print(out)
    else:
        print("[scale-gateway] ERROR: Docker scaling failed.")
        if out:
            print("STDOUT:", out)
        if err:
            print("STDERR:", err)

    return code


def scale_k8s(replicas: int) -> int:
    """
    Scale the FastAPI gateway when running under Kubernetes.

    Environment variables:
      - K8S_DEPLOYMENT_NAME: name of the Kubernetes Deployment
        (e.g. "cyberoracle-gateway"). REQUIRED.
      - K8S_NAMESPACE: Kubernetes namespace. Default: "default".
    """
    deployment = os.getenv("K8S_DEPLOYMENT_NAME")
    namespace = os.getenv("K8S_NAMESPACE", "default")

    if not deployment:
        print(
            "[scale-gateway] ERROR: K8S_DEPLOYMENT_NAME is not set. "
            "Set it to your FastAPI Deployment name (e.g. cyberoracle-gateway)."
        )
        return 1

    print(
        f"[scale-gateway] Target: Kubernetes | Deployment={deployment} | "
        f"Namespace={namespace} | Replicas={replicas}"
    )

    cmd = [
        "kubectl",
        "scale",
        f"deployment/{deployment}",
        f"--replicas={replicas}",
        "-n",
        namespace,
    ]

    code, out, err = run_command(cmd)

    if code == 0:
        print("[scale-gateway] Kubernetes scaling command completed successfully.")
        if out:
            print(out)
    else:
        print("[scale-gateway] ERROR: Kubernetes scaling failed.")
        if out:
            print("STDOUT:", out)
        if err:
            print("STDERR:", err)

    return code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PSFR8 – Ops automation script to scale CyberOracle gateway "
        "in Docker Compose or Kubernetes."
    )
    parser.add_argument(
        "--target",
        choices=["docker", "k8s"],
        default="docker",
        help="Scaling target: 'docker' (Docker Compose) or 'k8s' (Kubernetes). "
        "Default: docker.",
    )
    parser.add_argument(
        "--replicas",
        type=int,
        required=True,
        help="Desired number of replicas for the gateway service.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.replicas < 1:
        print("[scale-gateway] ERROR: replicas must be >= 1")
        return 1

    if args.target == "docker":
        return scale_docker(args.replicas)

    if args.target == "k8s":
        return scale_k8s(args.replicas)

    print(f"[scale-gateway] ERROR: Unknown target '{args.target}'")
    return 1


if __name__ == "__main__":
    sys.exit(main())
