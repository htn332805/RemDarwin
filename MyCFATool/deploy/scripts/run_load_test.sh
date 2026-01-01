#!/bin/bash

# MyCFATool Load Testing Script
# Runs performance and load tests against deployed application

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

# Check if application is accessible
check_application_access() {
    local env="$1"
    local alb_dns
    local url

    alb_dns=$(get_terraform_output "alb_dns_name" "$env")
    if [[ -z "$alb_dns" ]]; then
        error "ALB DNS name not found. Please run health check first."
        exit 1
    fi

    url="http://$alb_dns"

    log "Checking application accessibility at $url..."

    if ! curl -f -s "$url" &>/dev/null; then
        error "Application is not accessible at $url"
        exit 1
    fi

    log "Application is accessible."
}

# Install Locust if not present
install_locust() {
    if ! command -v locust &> /dev/null; then
        log "Installing Locust..."
        pip install locust
    fi
}

# Update Locust config for environment
update_locust_config() {
    local env="$1"
    local config_file="$PROJECT_ROOT/load_test_config.yaml"
    local alb_dns

    alb_dns=$(get_terraform_output "alb_dns_name" "$env")
    if [[ -z "$alb_dns" ]]; then
        error "ALB DNS name not found."
        exit 1
    fi

    # Update config file with current environment URL
    if [[ -f "$config_file" ]]; then
        sed -i.bak "s|host:.*|host: http://$alb_dns|" "$config_file"
        log "Updated Locust config with environment URL: http://$alb_dns"
    else
        warn "Load test config file not found: $config_file"
    fi
}

# Run load test
run_load_test() {
    local env="$1"
    local test_type="${2:-smoke}"
    local users="${3:-10}"
    local hatch_rate="${4:-2}"
    local run_time="${5:-1m}"

    log "Running $test_type load test..."
    log "Users: $users, Hatch rate: $hatch_rate, Run time: $run_time"

    cd "$PROJECT_ROOT"

    # Set environment variable for Locust
    export LOAD_TEST_ENV="$env"
    export LOAD_TEST_TYPE="$test_type"

    # Run Locust in headless mode
    locust \
        --locustfile locustfile.py \
        --host "http://$(get_terraform_output "alb_dns_name" "$env")" \
        --users "$users" \
        --spawn-rate "$hatch_rate" \
        --run-time "$run_time" \
        --headless \
        --only-summary \
        --csv results_"$env"_"$(date +%Y%m%d_%H%M%S)" \
        --logfile logs/locust_"$env"_$(date +%Y%m%d_%H%M%S).log

    log "Load test completed."
}

# Analyze results
analyze_results() {
    local env="$1"
    local test_type="$2"

    log "Analyzing load test results..."

    # Find the latest CSV results file
    local results_file
    results_file=$(find . -name "results_${env}_*.csv" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

    if [[ -z "$results_file" ]]; then
        warn "No results file found."
        return
    fi

    log "Results file: $results_file"

    # Parse and display key metrics
    if [[ -f "$results_file" ]]; then
        log "Key Performance Metrics:"
        echo "========================================"

        # Read the last line (summary)
        local summary
        summary=$(tail -1 "$results_file")
        IFS=',' read -r -a fields <<< "$summary"

        if [[ ${#fields[@]} -ge 8 ]]; then
            echo "Requests/sec: ${fields[1]}"
            echo "Failures/sec: ${fields[2]}"
            echo "Avg response time: ${fields[4]}ms"
            echo "95% response time: ${fields[6]}ms"
            echo "99% response time: ${fields[7]}ms"

            # Check against thresholds from config
            local config_file="$PROJECT_ROOT/load_test_config.yaml"
            if [[ -f "$config_file" ]]; then
                local thresholds
                thresholds=$(yq eval ".environments.$env.thresholds" "$config_file" 2>/dev/null || echo "")

                if [[ -n "$thresholds" ]]; then
                    local max_avg_response_time
                    local max_95p_response_time
                    local max_failure_rate

                    max_avg_response_time=$(echo "$thresholds" | yq eval ".max_avg_response_time" - 2>/dev/null || echo "1000")
                    max_95p_response_time=$(echo "$thresholds" | yq eval ".max_95p_response_time" - 2>/dev/null || echo "2000")
                    max_failure_rate=$(echo "$thresholds" | yq eval ".max_failure_rate" - 2>/dev/null || echo "0.05")

                    local avg_response_time="${fields[4]}"
                    local p95_response_time="${fields[6]}"
                    local failure_rate="${fields[2]}"

                    local passed=true

                    if (( $(echo "$avg_response_time > $max_avg_response_time" | bc -l 2>/dev/null || echo "0") )); then
                        error "Average response time ($avg_response_time ms) exceeds threshold ($max_avg_response_time ms)"
                        passed=false
                    fi

                    if (( $(echo "$p95_response_time > $max_95p_response_time" | bc -l 2>/dev/null || echo "0") )); then
                        error "95% response time ($p95_response_time ms) exceeds threshold ($max_95p_response_time ms)"
                        passed=false
                    fi

                    if (( $(echo "$failure_rate > $max_failure_rate" | bc -l 2>/dev/null || echo "0") )); then
                        error "Failure rate ($failure_rate) exceeds threshold ($max_failure_rate)"
                        passed=false
                    fi

                    if [[ "$passed" == "true" ]]; then
                        log "All performance thresholds met!"
                    fi
                fi
            fi
        fi

        echo "========================================"
    fi
}

# Run performance validation
run_performance_validation() {
    local env="$1"

    log "Running performance validation tests..."

    # Smoke test
    run_load_test "$env" "smoke" 5 5 "30s"

    # Light load test
    run_load_test "$env" "light" 20 5 "2m"

    # Medium load test (for staging)
    if [[ "$env" == "staging" ]]; then
        run_load_test "$env" "medium" 50 10 "5m"
    fi

    # Analyze results
    analyze_results "$env" "validation"
}

# Main function
main() {
    local env="${1:-staging}"
    local test_type="${2:-validation}"

    log "Starting MyCFATool load testing for environment: $env, type: $test_type"

    validate_environment "$env"
    check_application_access "$env"
    install_locust
    update_locust_config "$env"

    case "$test_type" in
        smoke)
            run_load_test "$env" "smoke" 5 5 "30s"
            ;;
        light)
            run_load_test "$env" "light" 20 5 "2m"
            ;;
        medium)
            run_load_test "$env" "medium" 50 10 "5m"
            ;;
        heavy)
            run_load_test "$env" "heavy" 100 20 "10m"
            ;;
        validation)
            run_performance_validation "$env"
            ;;
        *)
            error "Invalid test type: $test_type"
            echo "Valid types: smoke, light, medium, heavy, validation"
            exit 1
            ;;
    esac

    analyze_results "$env" "$test_type"

    log "Load testing completed."
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [test_type]"
    echo "  environment: staging (default) or production"
    echo "  test_type: validation (default), smoke, light, medium, heavy"
    echo ""
    echo "Test Types:"
    echo "  smoke    - Quick smoke test (5 users, 30s)"
    echo "  light    - Light load test (20 users, 2m)"
    echo "  medium   - Medium load test (50 users, 5m)"
    echo "  heavy    - Heavy load test (100 users, 10m)"
    echo "  validation - Full performance validation suite"
    echo ""
    echo "Examples:"
    echo "  $0 staging smoke"
    echo "  $0 production validation"
}

# Parse arguments
if [[ $# -gt 2 ]]; then
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