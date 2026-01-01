#!/bin/bash

# MyCFATool Health Check Script
# Validates successful deployment and application health

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

# Validate environment
validate_environment() {
    local env="$1"
    if [[ "$env" != "staging" && "$env" != "production" ]]; then
        error "Invalid environment: $env. Must be 'staging' or 'production'."
        exit 1
    fi
}

# Get Terraform outputs
get_terraform_output() {
    local output_name="$1"
    local env="$2"

    cd "$TERRAFORM_DIR"
    terraform output -json "$output_name" 2>/dev/null | jq -r . || echo ""
}

# Check Terraform state
check_terraform_state() {
    local env="$1"

    log "Checking Terraform state..."

    cd "$TERRAFORM_DIR"
    if ! terraform state list &>/dev/null; then
        error "Terraform state not found. Infrastructure may not be deployed."
        return 1
    fi

    log "Terraform state exists."
}

# Check AWS resources
check_aws_resources() {
    local env="$1"
    local region="us-east-1"

    log "Checking AWS resources..."

    # Check ECR repository
    local ecr_repo
    ecr_repo=$(get_terraform_output "ecr_repository_url" "$env")
    if [[ -z "$ecr_repo" ]]; then
        error "ECR repository not found in Terraform outputs."
        return 1
    fi

    local repo_name="${ecr_repo##*/}"
    if ! aws ecr describe-repositories --repository-names "$repo_name" --region "$region" &>/dev/null; then
        error "ECR repository $repo_name does not exist."
        return 1
    fi
    log "ECR repository exists."

    # Check ECS cluster
    local cluster_name
    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    if [[ -z "$cluster_name" ]]; then
        error "ECS cluster not found in Terraform outputs."
        return 1
    fi

    if ! aws ecs describe-clusters --clusters "$cluster_name" --region "$region" &>/dev/null; then
        error "ECS cluster $cluster_name does not exist."
        return 1
    fi
    log "ECS cluster exists."

    # Check secrets
    local secrets=(
        "secrets_arn_db_url"
        "secrets_arn_secret_key"
        "secrets_arn_fmp_api_key"
    )

    for secret_output in "${secrets[@]}"; do
        local secret_arn
        secret_arn=$(get_terraform_output "$secret_output" "$env")
        if [[ -z "$secret_arn" ]]; then
            error "Secret $secret_output not found in Terraform outputs."
            return 1
        fi

        if ! aws secretsmanager describe-secret --secret-id "$secret_arn" --region "$region" &>/dev/null; then
            error "Secret $secret_arn does not exist."
            return 1
        fi
    done
    log "All secrets exist."
}

# Check ECS service health
check_ecs_service() {
    local env="$1"
    local region="us-east-1"
    local cluster_name
    local service_name

    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    service_name="mycfatool-${env}-app-service"

    log "Checking ECS service health..."

    local service_status
    service_status=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$region" \
        --query 'services[0].status' \
        --output text 2>/dev/null || echo "UNKNOWN")

    if [[ "$service_status" != "ACTIVE" ]]; then
        error "ECS service status: $service_status"
        return 1
    fi
    log "ECS service is ACTIVE."

    # Check running tasks
    local running_count
    running_count=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$region" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "0")

    if [[ "$running_count" -lt 1 ]]; then
        error "No running tasks found. Running count: $running_count"
        return 1
    fi
    log "Running tasks: $running_count"

    # Check deployment status
    local rollout_state
    rollout_state=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$region" \
        --query 'services[0].deployments[0].rolloutState' \
        --output text 2>/dev/null || echo "UNKNOWN")

    if [[ "$rollout_state" != "COMPLETED" ]]; then
        warn "Deployment rollout state: $rollout_state"
        if [[ "$rollout_state" == "FAILED" ]]; then
            return 1
        fi
    else
        log "Deployment completed successfully."
    fi
}

# Check application health
check_application_health() {
    local env="$1"
    local alb_dns
    local url

    alb_dns=$(get_terraform_output "alb_dns_name" "$env")
    if [[ -z "$alb_dns" ]]; then
        error "ALB DNS name not found in Terraform outputs."
        return 1
    fi

    url="http://$alb_dns"

    log "Checking application health at $url..."

    # Wait for ALB to be ready
    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" &>/dev/null; then
            log "Application is responding."
            return 0
        fi

        log "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    error "Application health check failed after $max_attempts attempts."
    return 1
}

# Check database connectivity (basic)
check_database() {
    local env="$1"

    log "Checking database connectivity..."

    # Get database endpoint
    local db_endpoint
    db_endpoint=$(get_terraform_output "db_endpoint" "$env")
    if [[ -z "$db_endpoint" ]]; then
        error "Database endpoint not found in Terraform outputs."
        return 1
    fi

    # Try to connect (basic connectivity test)
    # Note: This is a simple TCP connection test, not a full database connection
    if nc -z -w5 "$db_endpoint" 5432 2>/dev/null; then
        log "Database port is accessible."
    else
        warn "Database port connectivity check failed. This may be expected if security groups restrict access."
    fi
}

# Generate health report
generate_report() {
    local env="$1"
    local report_file="/tmp/mycfatool-health-report-${env}-$(date +%Y%m%d-%H%M%S).txt"

    log "Generating health report: $report_file"

    {
        echo "MyCFATool Health Check Report"
        echo "Environment: $env"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""

        echo "Terraform State: $(cd "$TERRAFORM_DIR" && terraform state list | wc -l) resources"
        echo ""

        echo "AWS Resources:"
        echo "- ECR Repository: $(get_terraform_output "ecr_repository_url" "$env")"
        echo "- ECS Cluster: $(get_terraform_output "ecs_cluster_name" "$env")"
        echo "- ALB DNS: $(get_terraform_output "alb_dns_name" "$env")"
        echo ""

        echo "Secrets Status:"
        local secrets=(
            "DB URL:secrets_arn_db_url"
            "Secret Key:secrets_arn_secret_key"
            "FMP API Key:secrets_arn_fmp_api_key"
        )

        for secret in "${secrets[@]}"; do
            local name="${secret%%:*}"
            local output="${secret##*:}"
            local arn
            arn=$(get_terraform_output "$output" "$env")
            echo "- $name: ${arn:-NOT FOUND}"
        done
        echo ""

        echo "Report saved to: $report_file"

    } > "$report_file"

    log "Health report generated."
}

# Main health check function
main() {
    local env="${1:-staging}"
    local checks_passed=0
    local total_checks=0

    log "Starting MyCFATool health check for environment: $env"

    validate_environment "$env"

    # Run checks
    local checks=(
        "check_terraform_state"
        "check_aws_resources"
        "check_ecs_service"
        "check_application_health"
        "check_database"
    )

    for check in "${checks[@]}"; do
        ((total_checks++))
        if $check "$env"; then
            ((checks_passed++))
        fi
        echo ""
    done

    # Generate report
    generate_report "$env"

    # Summary
    echo "========================================"
    log "Health check summary: $checks_passed/$total_checks checks passed"

    if [[ $checks_passed -eq $total_checks ]]; then
        log "All health checks passed!"
        exit 0
    else
        error "Some health checks failed. Please review the output above."
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: staging (default) or production"
    echo ""
    echo "This script performs comprehensive health checks including:"
    echo "  - Terraform state validation"
    echo "  - AWS resource existence"
    echo "  - ECS service health"
    echo "  - Application HTTP response"
    echo "  - Database connectivity"
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