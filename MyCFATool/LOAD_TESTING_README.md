# MyCFATool Load Testing Guide

This guide provides comprehensive instructions for running load tests on the MyCFATool production deployment using Locust framework.

## Overview

The load testing suite simulates realistic user interactions with the MyCFATool dashboard, including:
- User authentication and session management
- Ticker selection and dropdown loading
- Financial data retrieval (statements, ratios, prices)
- Chart generation and technical analysis
- Portfolio analysis with multi-ticker operations
- PDF report generation

## Test Scenarios

### User Types
1. **LightUser**: Focuses on overview browsing and basic data viewing (60% of users)
2. **HeavyUser**: Performs deep technical analysis and portfolio creation (20% of users)
3. **MixedUser**: Combination of browsing and analysis activities (20% of users)

### Test Scenarios
- **Light Browsing**: Basic navigation and data viewing
- **Heavy Analysis**: Intensive data processing and analysis
- **Mixed Usage**: Balanced combination of activities

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure MyCFATool application is running (local or deployed)

3. Configure test data in `load_test_config.yaml`

## Configuration

### Environment Configuration

Edit `load_test_config.yaml` to configure different environments:

```yaml
environments:
  local:
    host: "http://localhost:8050"
    users: 10
    spawn_rate: 2
    run_time: "5m"
  staging:
    host: "https://staging-mycfatool.example.com"
    users: 25
    spawn_rate: 5
    run_time: "10m"
  production:
    host: "https://mycfatool.example.com"
    users: 50
    spawn_rate: 10
    run_time: "15m"
```

### Performance Thresholds

Configure acceptable performance thresholds:

```yaml
thresholds:
  response_time_95p: 2000  # 95th percentile < 2s
  response_time_99p: 5000  # 99th percentile < 5s
  failure_rate: 5.0        # Failure rate < 5%
```

## Execution Instructions

### Basic Local Testing

1. Start the MyCFATool application:
```bash
cd MyCFATool
python -m MyCFATool.dashboard.app
```

2. Run load test in another terminal:
```bash
locust -f locustfile.py --host=http://localhost:8050
```

3. Open http://localhost:8089 in browser to access Locust web UI

4. Configure test parameters and start testing

### Command Line Execution

#### Local Environment (10 users, 5 minutes)
```bash
locust -f locustfile.py \
  --host=http://localhost:8050 \
  --users=10 \
  --spawn-rate=2 \
  --run-time=5m \
  --html=load_test_report.html
```

#### Staging Environment (25 users, 10 minutes)
```bash
export LOCUST_ENV=staging
locust -f locustfile.py \
  --users=25 \
  --spawn-rate=5 \
  --run-time=10m \
  --html=staging_load_test_report.html
```

#### Production Environment (50 users, 15 minutes)
```bash
export LOCUST_ENV=production
locust -f locustfile.py \
  --users=50 \
  --spawn-rate=10 \
  --run-time=15m \
  --html=production_load_test_report.html
```

### Advanced Options

#### Custom User Classes
```bash
# Run only LightUser
locust -f locustfile.py --host=http://localhost:8050 --users=20 --spawn-rate=4 --class-picker=LightUser

# Run only HeavyUser
locust -f locustfile.py --host=http://localhost:8050 --users=5 --spawn-rate=1 --class-picker=HeavyUser
```

#### Headless Mode with CSV Output
```bash
locust -f locustfile.py \
  --headless \
  --users=20 \
  --spawn-rate=4 \
  --run-time=5m \
  --csv=load_test_results \
  --html=load_test_report.html
```

## Performance Metrics

The load tests collect and validate the following metrics:

### Response Time Metrics
- Average response time
- 95th percentile response time
- 99th percentile response time
- Min/Max response times

### Throughput Metrics
- Requests per second (RPS)
- Total requests
- Successful requests
- Failed requests

### Error Metrics
- Failure rate (%)
- HTTP error codes distribution

### Custom Timers
- Page navigation times
- Data loading times
- Chart generation times
- PDF generation times

## Threshold Validation

The test automatically validates performance against configured thresholds:

- **PASS**: All thresholds met
- **FAIL**: Any threshold exceeded

Example output:
```
Load Test Summary (production environment):
Total Requests: 15420
Total Failures: 231
Failure Rate: 1.5%
95th Percentile Response Time: 1850ms
99th Percentile Response Time: 3200ms
SUCCESS: All performance thresholds met!
```

## Test Results Analysis

### Interpreting Results

1. **Response Times**:
   - < 1000ms: Excellent
   - 1000-2000ms: Good
   - 2000-5000ms: Acceptable
   - > 5000ms: Poor

2. **Failure Rate**:
   - < 1%: Excellent
   - 1-5%: Acceptable
   - > 5%: Concerning

3. **RPS**: Should scale linearly with user count

### Common Issues

1. **High Response Times**:
   - Check database performance
   - Review application logs
   - Monitor server resources

2. **High Failure Rates**:
   - Check application error logs
   - Verify authentication setup
   - Ensure test data validity

3. **Memory Issues**:
   - Monitor application memory usage
   - Check for memory leaks
   - Consider horizontal scaling

## Scaling Considerations

### Database Load
- Monitor database connections
- Check query performance
- Consider read replicas for heavy loads

### Application Scaling
- Horizontal scaling with load balancer
- Session management in distributed setup
- Caching strategies

### Infrastructure
- Monitor CPU, memory, network
- Auto-scaling policies
- CDN for static assets

## Troubleshooting

### Common Errors

1. **Connection Refused**:
   - Ensure application is running
   - Check host and port configuration
   - Verify firewall settings

2. **Authentication Failures**:
   - Check test user credentials
   - Verify authentication endpoint
   - Review application logs

3. **Timeout Errors**:
   - Increase timeout settings
   - Check application performance
   - Monitor server resources

### Debug Mode

Enable debug logging:
```bash
locust -f locustfile.py --loglevel=DEBUG --host=http://localhost:8050
```

## Best Practices

1. **Gradual Load Increase**: Start with low user counts and gradually increase
2. **Realistic Scenarios**: Use wait times that simulate real user behavior
3. **Regular Testing**: Run load tests regularly during development and deployment
4. **Monitor Resources**: Track server resources during tests
5. **Baseline Comparison**: Compare results against established baselines

## Continuous Integration

### Automated Load Testing

Add to CI/CD pipeline:

```yaml
# .github/workflows/load-test.yml
name: Load Testing
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run Load Test
      run: |
        pip install -r requirements.txt
        locust -f locustfile.py --headless --users=10 --spawn-rate=2 --run-time=2m --csv=results
    - name: Upload Results
      uses: actions/upload-artifact@v2
      with:
        name: load-test-results
        path: results_*.csv
```

## Support

For issues or questions regarding load testing:

1. Check application logs during test runs
2. Review Locust documentation
3. Monitor system resources
4. Analyze test result reports

## Version History

- v1.0: Initial implementation with basic scenarios
- v1.1: Added performance thresholds and validation
- v1.2: Enhanced user scenarios and metrics collection