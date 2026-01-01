#!/bin/bash

# MyCFATool Rollback Script
# Rolls back deployment to previous stable version

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

# Check current deployment status
check_deployment_status() {
    local env="$1"
    local region="us-east-1"
    local cluster_name
    local service_name

    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    service_name="mycfatool-${env}-app-service"

    log "Checking current deployment status..."

    local deployments
    deployments=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$region" \
        --query 'services[0].deployments' \
        --output json 2>/dev/null || echo "[]")

    local deployment_count
    deployment_count=$(echo "$deployments" | jq length)

    if [[ $deployment_count -eq 0 ]]; then
        error "No deployments found for service $service_name"
        return 1
    fi

    log "Found $deployment_count deployment(s)"

    # Show deployment details
    echo "$deployments" | jq -r '.[] | "Task Definition: \(.taskDefinition | split("/")[-1]), Status: \(.status), Rollout: \(.rolloutState), Running: \(.runningCount)/\(.desiredCount)"'

    # Check for failed deployments
    local failed_count
    failed_count=$(echo "$deployments" | jq '[.[] | select(.rolloutState == "FAILED")] | length')

    if [[ $failed_count -gt 0 ]]; then
        warn "Found $failed_count failed deployment(s)"
        return 1
    fi

    log "Current deployment status is healthy."
}

# Find previous stable task definition
find_previous_task_definition() {
    local env="$1"
    local region="us-east-1"
    local cluster_name
    local service_name

    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    service_name="mycfatool-${env}-app-service"

    log "Finding previous stable task definition..."

    # Get service details to find previous task definition
    local service_details
    service_details=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$region" \
        --query 'services[0]' \
        --output json 2>/dev/null)

    if [[ -z "$service_details" ]]; then
        error "Could not get service details"
        return 1
    fi

    # Get current task definition
    local current_td
    current_td=$(echo "$service_details" | jq -r '.taskDefinition')

    log "Current task definition: $current_td"

    # List task definitions for this family
    local family="mycfatool-${env}-app"
    local task_defs
    task_defs=$(aws ecs list-task-definitions \
        --family-prefix "$family" \
        --region "$region" \
        --sort DESC \
        --query 'taskDefinitionArns' \
        --output json 2>/dev/null | jq -r '.[]')

    if [[ -z "$task_defs" ]]; then
        error "No task definitions found for family $family"
        return 1
    fi

    # Find the previous one
    local previous_td=""
    local found_current=false

    while IFS= read -r td; do
        if [[ "$found_current" == "true" ]]; then
            previous_td="$td"
            break
        fi
        if [[ "$td" == "$current_td" ]]; then
            found_current=true
        fi
    done <<< "$task_defs"

    if [[ -z "$previous_td" ]]; then
        error "No previous task definition found"
        return 1
    fi

    log "Previous task definition: $previous_td"
    echo "$previous_td"
}

# Perform rollback
perform_rollback() {
    local env="$1"
    local region="us-east-1"
    local cluster_name
    local service_name
    local previous_td

    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    service_name="mycfatool-${env}-app-service"

    previous_td=$(find_previous_task_definition "$env")

    log "Rolling back to previous task definition: $previous_td"

    # Update service to use previous task definition
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --task-definition "$previous_td" \
        --region "$region" \
        --query 'service.serviceName' \
        --output text

    log "Rollback initiated. Waiting for deployment to complete..."

    # Wait for deployment to complete
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local rollout_state
        rollout_state=$(aws ecs describe-services \
            --cluster "$cluster_name" \
            --services "$service_name" \
            --region "$region" \
            --query 'services[0].deployments[0].rolloutState' \
            --output text 2>/dev/null || echo "UNKNOWN")

        if [[ "$rollout_state" == "COMPLETED" ]]; then
            log "Rollback completed successfully."
            return 0
        elif [[ "$rollout_state" == "FAILED" ]]; then
            error "Rollback failed."
            return 1
        fi

        log "Waiting for rollback... (attempt $attempt/$max_attempts)"
        sleep 30
        ((attempt++))
    done

    error "Timeout waiting for rollback to complete."
    return 1
}

# Verify rollback
verify_rollback() {
    local env="$1"

    log "Verifying rollback..."

    # Run health check
    if "$SCRIPT_DIR/health_check.sh" "$env" &>/dev/null; then
        log "Rollback verification passed."
        return 0
    else
        error "Rollback verification failed."
        return 1
    fi
}

# Create incident report
create_incident_report() {
    local env="$1"
    local reason="$2"
    local report_file="/tmp/mycfatool-rollback-report-${env}-$(date +%Y%m%d-%H%M%S).txt"

    log "Creating incident report: $report_file"

    {
        echo "MyCFATool Rollback Incident Report"
        echo "Environment: $env"
        echo "Timestamp: $(date)"
        echo "Reason: $reason"
        echo "========================================"
        echo ""
        echo "Deployment Status Before Rollback:"
        check_deployment_status "$env" 2>&1 | grep -v "Checking current deployment status"
        echo ""
        echo "Rollback Actions Taken:"
        echo "- Reverted to previous task definition"
        echo "- Updated ECS service"
        echo "- Monitored deployment completion"
        echo ""
        echo "Verification Results:"
        if verify_rollback "$env" 2>&1; then
            echo "✓ Health checks passed"
        else
            echo "✗ Health checks failed"
        fi
        echo ""
        echo "Next Steps:"
        echo "1. Investigate root cause of deployment failure"
        echo "2. Fix issues in codebase"
        echo "3. Test fixes in staging environment"
        echo "4. Redeploy to production"
        echo ""
        echo "Report saved to: $report_file"

    } > "$report_file"

    log "Incident report created."
}

# Force rollback (emergency)
force_rollback() {
    local env="$1"
    local region="us-east-1"
    local cluster_name
    local service_name

    cluster_name=$(get_terraform_output "ecs_cluster_name" "$env")
    service_name="mycfatool-${env}-app-service"

    warn "Performing emergency rollback - this will stop all tasks immediately!"

    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Emergency rollback cancelled."
        exit 0
    fi

    # Scale service to 0
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --desired-count 0 \
        --region "$region"

    log "Scaled service to 0 tasks."

    # Find and use the oldest stable task definition
    local family="mycfatool-${env}-app"
    local oldest_td
    oldest_td=$(aws ecs list-task-definitions \
        --family-prefix "$family" \
        --region "$region" \
        --query 'taskDefinitionArns[0]' \
        --output text 2>/dev/null)

    if [[ -z "$oldest_td" ]]; then
        error "No stable task definition found for emergency rollback"
        return 1
    fi

    log "Using oldest stable task definition: $oldest_td"

    # Update service with old task definition
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --task-definition "$oldest_td" \
        --desired-count 2 \
        --region "$region"

    log "Emergency rollback completed. Service scaled back to 2 tasks."
}

# Main rollback function
main() {
    local env="${1:-staging}"
    local force="${2:-false}"
    local reason="${3:-Manual rollback request}"

    log "Starting MyCFATool rollback for environment: $env"

    validate_environment "$env"

    # Check current status
    if ! check_deployment_status "$env"; then
        if [[ "$force" == "true" ]]; then
            log "Deployment issues detected. Proceeding with forced rollback."
            force_rollback "$env"
        else
            log "Deployment issues detected. Attempting graceful rollback."
            if perform_rollback "$env"; then
                verify_rollback "$env"
                create_incident_report "$env" "$reason"
                log "Rollback completed successfully."
            else
                error "Graceful rollback failed. Consider using --force option."
                exit 1
            fi
        fi
    else
        log "Current deployment appears healthy. No rollback needed."
        log "If you still want to rollback, use --force option."
        exit 0
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [--force] [reason]"
    echo "  environment: staging (default) or production"
    echo "  --force: Perform emergency rollback (scales to 0 then back)"
    echo "  reason: Reason for rollback (default: 'Manual rollback request')"
    echo ""
    echo "This script performs rollback operations including:"
    echo "  - Check current deployment status"
    echo "  - Find previous stable task definition"
    echo "  - Update ECS service to use previous version"
    echo "  - Wait for deployment completion"
    echo "  - Verify application health"
    echo "  - Generate incident report"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  $0 production --force \"Application crash\""
}

# Parse arguments
if [[ $# -gt 3 ]]; then
    usage
    exit 1
fi

force_rollback=false
env="staging"
reason="Manual rollback request"

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            force_rollback=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [[ "$1" == "staging" || "$1" == "production" ]]; then
                env="$1"
            else
                reason="$1"
            fi
            shift
            ;;
    esac
done

main "$env" "$force_rollback" "$reason"