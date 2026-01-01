#!/bin/bash

# MyCFATool Deployment Script
# Supports staging and production environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TERRAFORM_DIR="$PROJECT_ROOT/deploy/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
        exit 1
    fi

    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install it first."
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI is not configured or credentials are invalid."
        exit 1
    fi

    log "Prerequisites check passed."
}

# Validate environment
validate_environment() {
    local env="$1"
    if [[ "$env" != "staging" && "$env" != "production" ]]; then
        error "Invalid environment: $env. Must be 'staging' or 'production'."
        exit 1
    fi
}

# Build and push Docker image
build_and_push_image() {
    local env="$1"
    local account_id
    local region="us-east-1"
    local repo_name="mycfatool-${env}"

    log "Building and pushing Docker image..."

    account_id=$(aws sts get-caller-identity --query Account --output text)

    # Login to ECR
    aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$account_id.dkr.ecr.$region.amazonaws.com"

    # Build image
    docker build -t "$repo_name" "$PROJECT_ROOT"

    # Tag image
    docker tag "$repo_name:latest" "$account_id.dkr.ecr.$region.amazonaws.com/$repo_name:latest"

    # Push image
    docker push "$account_id.dkr.ecr.$region.amazonaws.com/$repo_name:latest"

    log "Docker image pushed successfully."
}

# Deploy infrastructure
deploy_infrastructure() {
    local env="$1"

    log "Deploying infrastructure with Terraform..."

    cd "$TERRAFORM_DIR"

    # Initialize Terraform
    terraform init

    # Validate configuration
    terraform validate

    # Plan deployment
    terraform plan -var "environment=$env" -out=tfplan

    # Apply changes
    terraform apply tfplan

    log "Infrastructure deployment completed."
}

# Wait for service to be healthy
wait_for_service() {
    local env="$1"
    local cluster_name="mycfatool-${env}-cluster"
    local service_name="mycfatool-${env}-app-service"
    local region="us-east-1"

    log "Waiting for ECS service to be healthy..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local status
        status=$(aws ecs describe-services \
            --cluster "$cluster_name" \
            --services "$service_name" \
            --region "$region" \
            --query 'services[0].deployments[0].rolloutState' \
            --output text 2>/dev/null || echo "FAILED")

        if [[ "$status" == "COMPLETED" ]]; then
            log "ECS service is healthy."
            return 0
        elif [[ "$status" == "FAILED" ]]; then
            error "ECS service deployment failed."
            return 1
        fi

        log "Waiting for service... (attempt $attempt/$max_attempts)"
        sleep 30
        ((attempt++))
    done

    error "Timeout waiting for ECS service to be healthy."
    return 1
}

# Main deployment function
main() {
    local env="${1:-staging}"

    log "Starting MyCFATool deployment for environment: $env"

    validate_environment "$env"
    check_prerequisites
    build_and_push_image "$env"
    deploy_infrastructure "$env"
    wait_for_service "$env"

    log "Deployment completed successfully!"
    log "Application should be available at the ALB DNS name."
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: staging (default) or production"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  $0 production"
}

# Parse arguments
if [[ $# -gt 1 ]]; then
    usage
    exit 1
fi

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac