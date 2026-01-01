#!/bin/bash

# MyCFATool Secrets Setup Script
# Sets up AWS Secrets Manager secrets for database credentials and API keys

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
    terraform output -json "$output_name" | jq -r .
}

# Setup database URL secret
setup_db_secret() {
    local env="$1"
    local db_endpoint
    local db_port
    local db_name
    local db_username
    local db_password
    local db_url
    local secret_arn

    log "Setting up database URL secret..."

    # Get Terraform outputs
    db_endpoint=$(get_terraform_output "db_endpoint" "$env")
    db_port=$(get_terraform_output "db_port" "$env")
    db_name=$(get_terraform_output "db_name" "$env")
    secret_arn=$(get_terraform_output "secrets_arn_db_url" "$env")

    # Prompt for database credentials
    read -p "Enter database username: " db_username
    read -s -p "Enter database password: " db_password
    echo ""

    # Construct database URL
    db_url="postgresql://${db_username}:${db_password}@${db_endpoint}:${db_port}/${db_name}"

    # Update secret
    aws secretsmanager update-secret \
        --secret-id "$secret_arn" \
        --secret-string "$db_url" \
        --description "Database connection URL for MyCFATool $env"

    log "Database URL secret updated successfully."
}

# Setup Flask secret key
setup_secret_key() {
    local env="$1"
    local secret_arn

    log "Setting up Flask secret key..."

    secret_arn=$(get_terraform_output "secrets_arn_secret_key" "$env")

    # Generate a random secret key
    local secret_key
    secret_key=$(openssl rand -hex 32)

    # Update secret
    aws secretsmanager update-secret \
        --secret-id "$secret_arn" \
        --secret-string "$secret_key" \
        --description "Flask secret key for MyCFATool $env"

    log "Flask secret key set successfully."
    warn "Generated secret key: $secret_key"
    warn "Please save this key securely!"
}

# Setup FMP API key
setup_fmp_api_key() {
    local env="$1"
    local secret_arn

    log "Setting up FMP API key..."

    secret_arn=$(get_terraform_output "secrets_arn_fmp_api_key" "$env")

    # Prompt for FMP API key
    read -p "Enter FMP API key: " fmp_api_key

    # Update secret
    aws secretsmanager update-secret \
        --secret-id "$secret_arn" \
        --secret-string "$fmp_api_key" \
        --description "FMP API key for MyCFATool $env"

    log "FMP API key set successfully."
}

# Verify secrets
verify_secrets() {
    local env="$1"

    log "Verifying secrets setup..."

    local secrets=(
        "secrets_arn_db_url"
        "secrets_arn_secret_key"
        "secrets_arn_fmp_api_key"
    )

    for secret_output in "${secrets[@]}"; do
        local secret_arn
        secret_arn=$(get_terraform_output "$secret_output" "$env")

        if aws secretsmanager describe-secret --secret-id "$secret_arn" &>/dev/null; then
            log "Secret $secret_output exists."
        else
            error "Secret $secret_output does not exist."
            return 1
        fi
    done

    log "All secrets verified successfully."
}

# Main setup function
main() {
    local env="${1:-staging}"

    log "Starting MyCFATool secrets setup for environment: $env"

    validate_environment "$env"

    # Check if Terraform state exists
    cd "$TERRAFORM_DIR"
    if ! terraform state list &>/dev/null; then
        error "Terraform state not found. Please run deployment first."
        exit 1
    fi

    setup_db_secret "$env"
    setup_secret_key "$env"
    setup_fmp_api_key "$env"
    verify_secrets "$env"

    log "Secrets setup completed successfully!"
    warn "You can now run the deployment script."
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: staging (default) or production"
    echo ""
    echo "This script will:"
    echo "  - Prompt for database credentials"
    echo "  - Generate a Flask secret key"
    echo "  - Prompt for FMP API key"
    echo "  - Update AWS Secrets Manager secrets"
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