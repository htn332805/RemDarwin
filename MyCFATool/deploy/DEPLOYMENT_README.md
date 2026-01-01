# MyCFATool Production Deployment Guide

This document provides comprehensive instructions for deploying MyCFATool to AWS production using Terraform and ECS Fargate.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Secrets Management](#secrets-management)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Health Verification](#health-verification)
7. [Load Testing](#load-testing)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

## Prerequisites

### Required Tools

- AWS CLI (configured with appropriate permissions)
- Terraform >= 1.0
- Docker
- Git
- jq (for JSON processing)
- curl

### AWS Permissions

Ensure your AWS user/role has the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:*",
                "ecs:*",
                "rds:*",
                "secretsmanager:*",
                "iam:*",
                "kms:*",
                "elasticloadbalancing:*",
                "logs:*",
                "cloudwatch:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Required Secrets/APIs

- FMP API Key
- Database credentials (will be generated)

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd MyCFATool
```

2. Configure AWS CLI:
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region (us-east-1)
```

3. Verify AWS configuration:
```bash
aws sts get-caller-identity
```

## Secrets Management

Before deploying infrastructure, set up the required secrets in AWS Secrets Manager.

```bash
# Run the secrets setup script
./deploy/scripts/setup_secrets.sh [environment]
```

The script will:
- Prompt for database username and password
- Generate a Flask secret key
- Prompt for FMP API key
- Create/update secrets in AWS Secrets Manager

Example:
```bash
./deploy/scripts/setup_secrets.sh staging
```

## Infrastructure Deployment

Deploy the complete infrastructure using Terraform:

```bash
# Run the deployment script
./deploy/scripts/deploy.sh [environment]
```

Example for staging:
```bash
./deploy/scripts/deploy.sh staging
```

The script performs:
1. Builds Docker image
2. Pushes to ECR
3. Initializes Terraform
4. Plans infrastructure changes
5. Applies infrastructure
6. Waits for ECS service to be healthy

### What Gets Created

- VPC with private subnets
- RDS PostgreSQL database (encrypted)
- ECS cluster and service
- Application Load Balancer
- ECR repository
- Security groups and IAM roles
- CloudWatch logs
- Secrets Manager secrets

### Environment Variables

The deployment supports two environments:
- `staging`: Smaller instance sizes, for testing
- `production`: Production-grade sizing with redundancy

## Application Deployment

The deployment script handles application deployment automatically. For manual updates:

1. Build and push new image:
```bash
# The deployment script does this automatically
docker build -t mycfatool-staging .
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag mycfatool-staging:latest <account>.dkr.ecr.us-east-1.amazonaws.com/mycfatool-staging:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/mycfatool-staging:latest
```

2. Update ECS service:
```bash
# This is also handled automatically by the deployment script
aws ecs update-service --cluster mycfatool-staging-cluster --service mycfatool-staging-app-service --force-new-deployment
```

## Health Verification

After deployment, verify everything is working:

```bash
# Run comprehensive health checks
./deploy/scripts/health_check.sh [environment]
```

The health check verifies:
- Terraform state integrity
- AWS resource existence
- ECS service health
- Application HTTP response
- Database connectivity
- Generates a health report

Example output:
```
[INFO] Terraform state exists.
[INFO] ECR repository exists.
[INFO] ECS cluster exists.
[INFO] ECS service is ACTIVE.
[INFO] Running tasks: 2
[INFO] Application is responding.
[INFO] Database port is accessible.
[INFO] All health checks passed!
```

## Load Testing

Run performance tests against the deployed application:

```bash
# Run validation test suite
./deploy/scripts/run_load_test.sh [environment] validation
```

Available test types:
- `smoke`: Quick 5-user test (30 seconds)
- `light`: 20 users for 2 minutes
- `medium`: 50 users for 5 minutes (staging only)
- `heavy`: 100 users for 10 minutes
- `validation`: Full performance validation suite

Example:
```bash
./deploy/scripts/run_load_test.sh production validation
```

The script will:
- Update Locust config with environment URL
- Run tests with different load levels
- Analyze results against performance thresholds
- Generate CSV reports and logs

### Performance Thresholds

Defined in `load_test_config.yaml`:
- Max average response time: 1000ms
- Max 95% response time: 2000ms
- Max failure rate: 5%

## Monitoring and Maintenance

### CloudWatch Monitoring

- ECS service metrics
- ALB access logs
- Application logs
- RDS performance insights

### Log Locations

- Application logs: `/ecs/mycfatool-[env]-app`
- ECS events: CloudWatch Events
- ALB logs: S3 bucket (auto-created)

### Scheduled Maintenance

- Daily data ingestion (via scheduler)
- Weekly backups (RDS automated)
- Monthly security patching (ECS managed)

## Troubleshooting

### Common Issues

1. **Deployment fails during Terraform apply**
   - Check AWS limits (EC2 instances, RDS instances, etc.)
   - Verify VPC/subnet configuration
   - Check IAM permissions

2. **ECS service fails to start**
   - Check CloudWatch logs for application errors
   - Verify secrets are accessible
   - Check database connectivity

3. **Application returns 5xx errors**
   - Check application logs
   - Verify database connection
   - Check FMP API key validity

4. **Load balancer health checks fail**
   - Verify application responds on port 8050
   - Check security groups
   - Check ECS task networking

### Debugging Commands

```bash
# Check ECS service events
aws ecs describe-services --cluster mycfatool-staging-cluster --services mycfatool-staging-app-service --query 'services[0].events[0:5]'

# View application logs
aws logs tail /ecs/mycfatool-staging-app --follow

# Check task status
aws ecs list-tasks --cluster mycfatool-staging-cluster
aws ecs describe-tasks --cluster mycfatool-staging-cluster --tasks <task-id>

# Test database connectivity
aws rds describe-db-instances --db-instance-identifier mycfatool-staging
```

## Rollback Procedures

If deployment fails or issues are detected:

```bash
# Graceful rollback to previous version
./deploy/scripts/rollback.sh [environment]
```

For emergency situations:
```bash
# Force rollback (scales to 0 then back)
./deploy/scripts/rollback.sh [environment] --force "Emergency rollback"
```

The rollback script:
1. Identifies failed deployment
2. Finds previous stable task definition
3. Updates ECS service
4. Waits for deployment completion
5. Verifies application health
6. Generates incident report

### Rollback Scenarios

- **Application crashes**: Automatic rollback via circuit breaker
- **Performance degradation**: Manual rollback after load testing
- **Data corruption**: Emergency rollback + database restore
- **Security incident**: Immediate rollback + investigation

## Deployment Checklist

### Pre-Deployment
- [ ] AWS credentials configured
- [ ] Prerequisites installed
- [ ] Code tested locally
- [ ] Secrets prepared
- [ ] FMP API key available

### During Deployment
- [ ] Secrets setup completed
- [ ] Infrastructure deployed successfully
- [ ] Application deployed and healthy
- [ ] Load balancer accessible

### Post-Deployment
- [ ] Health checks passed
- [ ] Load tests completed
- [ ] Monitoring configured
- [ ] Team notified of deployment
- [ ] Documentation updated

## Cost Optimization

### Staging Environment
- t3.small ECS tasks
- db.r6g.large RDS (can be stopped when not in use)

### Production Environment
- t3.medium ECS tasks (2 instances)
- db.r6g.xlarge RDS with Multi-AZ
- Reserved instances for cost savings

### Auto Scaling

ECS service can be configured to scale based on:
- CPU utilization
- Memory utilization
- ALB request count

## Security Considerations

- All data encrypted at rest (RDS, Secrets Manager)
- VPC isolation with security groups
- IAM least-privilege access
- Secrets rotation (automated)
- Regular security patching
- ALB with HTTPS (certificate needed for production)

## Support

For issues or questions:
1. Check this documentation
2. Review application logs
3. Check AWS service health
4. Contact DevOps team

---

**Note**: This deployment uses infrastructure as code principles. All changes should be made through Terraform and committed to version control.