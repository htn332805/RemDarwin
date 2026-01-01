# MyCFATool Production Deployment Architecture

## Overview

This document outlines the comprehensive production deployment strategy for MyCFATool, transitioning from testing to full production operations supporting the complete S&P 500 ticker set (~500 tickers). The architecture leverages AWS cloud infrastructure with containerized deployment, implements robust API rate limiting, and optimizes for concurrent user access and database performance.

## Current System Architecture Summary

### Components
- **Data Ingestion**: FMP API client with batch processing capability
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support, JSON columns for flexible financial data storage
- **Dashboard**: Dash-based web application with multi-ticker portfolio analysis
- **Analytics**: Service layer with fundamental analysis, valuation, forecasting, and technical indicators
- **Scheduler**: APScheduler for automated batch data updates

### Key Constraints
- FMP API rate limit: 120 requests per minute
- Current batch ingestion: sequential processing (max_concurrent: 1)
- Database: ~500 tickers × multiple financial statements per ticker
- Dashboard: User-interactive analytics with real-time data queries

## Production Requirements & Constraints

### Data Volume Requirements
- **Tickers**: 500+ S&P 500 constituents
- **Data Types**: Income statements, balance sheets, cash flow, ratios, historical prices (annual + quarterly)
- **Update Frequency**: Weekly batch updates, daily price updates
- **Storage Estimate**: ~50-100GB for full dataset (JSON flexibility allows variable sizes)

### Performance Requirements
- **API Rate Limiting**: Must respect 120 req/min limit across batch ingestion
- **Concurrent Users**: Support 10-50 concurrent dashboard users
- **Query Response Time**: <2 seconds for dashboard queries
- **Batch Ingestion Time**: Complete weekly updates within 24-48 hours

### Operational Requirements
- **Availability**: 99.5% uptime
- **Scalability**: Auto-scale during peak usage
- **Monitoring**: Comprehensive logging, alerting, and metrics
- **Security**: Encrypted data, secure access, compliance-ready

## Infrastructure Components

### AWS Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│   ALB/EC2       │────│     RDS         │
│   (CDN + WAF)   │    │   (App Servers) │    │ (PostgreSQL DB) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   ECS Fargate   │
                    │ (Batch Workers) │
                    └─────────────────┘
```

#### 1. Database Layer (AWS RDS)
- **Engine**: PostgreSQL 15.x
- **Instance Class**: db.r6g.xlarge (4 vCPU, 32GB RAM) - scalable to larger as needed
- **Storage**: 500GB gp3 SSD with auto-scaling
- **Multi-AZ**: Enabled for high availability
- **Backup**: Automated daily backups with 7-day retention
- **Read Replicas**: 1-2 replicas for read-heavy dashboard queries

**Configuration**:
```yaml
database:
  type: postgresql
  host: mycfatool-prod.cluster-xyz.us-east-1.rds.amazonaws.com
  port: 5432
  name: mycfatool
  sslmode: require
  connection_pool:
    min: 5
    max: 20
    timeout: 30
```

#### 2. Application Layer (AWS EC2/ECS)
- **Compute**: ECS Fargate for serverless containers
- **Instance Types**: Varies based on load (Fargate tasks with 1-4 vCPU, 2-16GB RAM)
- **Auto Scaling**: Target CPU utilization 70%, min 2 tasks, max 10 tasks
- **Load Balancer**: Application Load Balancer with health checks

#### 3. Batch Processing (AWS ECS)
- **Dedicated Service**: Separate ECS cluster for data ingestion
- **Scheduled Tasks**: EventBridge rules for weekly/daily batch jobs
- **Spot Instances**: Use Fargate Spot for cost optimization during batch windows

#### 4. CDN & Security (AWS CloudFront)
- **Distribution**: Global CDN for static assets and API responses
- **WAF**: Web Application Firewall for protection against common attacks
- **SSL**: ACM certificates for HTTPS everywhere

## Scaling Approaches

### Horizontal Scaling Strategy
1. **Application Tier**:
   - ECS Fargate tasks auto-scale based on CPU/memory metrics
   - ALB distributes traffic across healthy instances
   - Session affinity for Dash app state management

2. **Database Tier**:
   - Read replicas for query-heavy operations
   - Connection pooling with SQLAlchemy
   - Query result caching with Redis (optional)

3. **Ingestion Tier**:
   - Parallel processing within API rate limits
   - Queue-based processing with SQS (future enhancement)
   - Time-windowed scheduling to avoid rate limit violations

### Vertical Scaling Considerations
- Database instance sizing based on data volume growth
- Memory optimization for large dataset queries
- CPU allocation for compute-intensive analytics

## Security Considerations

### Network Security
- **VPC**: Isolated VPC with public/private subnets
- **Security Groups**: Minimal required access rules
- **NACLs**: Network ACLs for subnet-level protection

### Data Security
- **Encryption**: Data-at-rest with KMS, in-transit with TLS 1.3
- **Secrets Management**: AWS Secrets Manager for API keys and credentials
- **IAM**: Least-privilege roles for ECS tasks and RDS access

### Application Security
- **Authentication**: Flask-Login with secure session management
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive validation for all user inputs
- **CSRF Protection**: Enabled for all forms

### Compliance
- **Data Residency**: AWS regions compliant with financial data regulations
- **Audit Logging**: All access and data modifications logged
- **Backup Encryption**: Encrypted backups with cross-region replication

## Operational Monitoring

### Metrics & Monitoring
- **CloudWatch**: Comprehensive monitoring for all AWS services
- **Custom Metrics**:
  - API rate limit usage
  - Batch ingestion success/failure rates
  - Query performance metrics
  - User session activity

### Logging Strategy
- **Centralized Logging**: CloudWatch Logs with retention policies
- **Log Levels**: ERROR for production, DEBUG for troubleshooting
- **Structured Logging**: JSON format for searchability

### Alerting
- **Critical Alerts**: Database connectivity issues, API failures
- **Performance Alerts**: High latency, rate limit approaching
- **Business Alerts**: Data ingestion failures, user impact

## Docker Containerization

### Base Images
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Application image
FROM base as app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "MyCFATool.dashboard.app:server"]
```

### Docker Compose for Development
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8050:8050"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mycfatool
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mycfatool
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Database Optimization

### Schema Optimizations
- **Indexing Strategy**: Composite indexes on (ticker_id, period_type, fiscal_date)
- **Partitioning**: Table partitioning by fiscal_year for large tables
- **JSON Optimization**: GIN indexes for JSON columns where needed

### Query Optimizations
- **Connection Pooling**: SQLAlchemy with proper pool sizing
- **Query Caching**: Redis for frequently accessed computed ratios
- **Batch Operations**: Bulk inserts/updates for ingestion
- **Read Optimization**: Use read replicas for dashboard queries

### Performance Configurations
```sql
-- PostgreSQL optimizations
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

## API Management & Rate Limiting

### Rate Limiting Implementation
- **Token Bucket Algorithm**: Distributed rate limiting with Redis
- **Per-API Key Limits**: Respect FMP's 120 req/min limit
- **Backoff Strategy**: Exponential backoff on rate limit hits

```python
# Rate limiter implementation
from redis import Redis
import time

class RateLimiter:
    def __init__(self, redis_client: Redis, key_prefix: str = "fmp"):
        self.redis = redis_client
        self.prefix = key_prefix
        self.limit = 120  # requests per minute
        self.window = 60  # seconds

    def allow_request(self, api_key: str) -> bool:
        key = f"{self.prefix}:{api_key}"
        now = time.time()
        window_start = now - self.window
        
        # Clean old requests
        self.redis.zremrangebyscore(key, '-inf', window_start)
        
        # Check current count
        count = self.redis.zcard(key)
        if count >= self.limit:
            return False
            
        # Add new request
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, self.window)
        return True
```

### Batch Processing Optimization
- **Concurrent Processing**: Limited concurrency to stay under rate limits
- **Scheduling**: Distribute requests over time windows
- **Error Handling**: Retry logic with backoff for transient failures

## Load Testing Strategy

### Test Scenarios
1. **Concurrent Users**: 50 users accessing dashboard simultaneously
2. **Data Ingestion**: Batch processing of 500 tickers
3. **Mixed Load**: Users + background ingestion

### Load Testing Tools
- **Locust**: For user simulation
- ** Artillery**: For API load testing
- **Custom Scripts**: For ingestion performance testing

### Performance Targets
- Response Time: <2s for 95th percentile
- Throughput: 100+ concurrent users
- Error Rate: <1%

## Deployment Strategy

### CI/CD Pipeline
- **GitHub Actions**: Automated testing and deployment
- **AWS CodePipeline**: Infrastructure as Code with CloudFormation
- **Blue-Green Deployment**: Zero-downtime deployments

### Environment Strategy
- **Development**: Local Docker development
- **Staging**: Full AWS environment for testing
- **Production**: Production-optimized configuration

### Configuration Management
- **Environment Variables**: For secrets and environment-specific config
- **AWS Systems Manager**: Parameter Store for configuration
- **Feature Flags**: For gradual rollout of new features

## Cost Optimization

### Reserved Instances
- RDS Reserved Instance for steady database workload
- Compute Savings Plans for ECS tasks

### Auto Scaling
- Scale down during off-peak hours
- Spot instances for batch processing

### Storage Optimization
- Data lifecycle policies for old backups
- Compression for historical data

## Migration Plan

### Phase 1: Infrastructure Setup
- Provision AWS resources with CloudFormation
- Set up CI/CD pipelines
- Deploy to staging environment

### Phase 2: Data Migration
- Migrate from SQLite to PostgreSQL
- Validate data integrity
- Optimize queries

### Phase 3: Application Deployment
- Deploy containerized application
- Configure monitoring and alerting
- Load testing validation

### Phase 4: Go-Live
- DNS cutover
- Monitor performance
- Post-launch optimization

## Risk Mitigation

### High Availability
- Multi-AZ deployment
- Automated failover
- Backup and recovery procedures

### Disaster Recovery
- Cross-region backup replication
- Recovery Time Objective: 4 hours
- Recovery Point Objective: 1 hour

### Security Incident Response
- Incident response plan
- Security monitoring
- Regular security assessments

This architecture provides a scalable, secure, and maintainable foundation for MyCFATool's production deployment, designed to handle the full S&P 500 dataset while maintaining performance and reliability standards.