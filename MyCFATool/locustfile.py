from locust import HttpUser, task, between, events
from locust.exception import StopUser
import random
import json
import yaml
import os

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'load_test_config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Environment from command line or default to local
ENVIRONMENT = os.environ.get('LOCUST_ENV', 'local')
env_config = config['environments'][ENVIRONMENT]
SAMPLE_TICKERS = config['test_data']['sample_tickers']
TEST_USERS = config['test_data']['test_users']

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Validate performance thresholds when test stops"""
    thresholds = env_config['thresholds']

    # Get stats
    stats = environment.stats
    total_requests = stats.num_requests
    total_failures = stats.num_failures
    response_times = stats.response_times

    # Calculate percentiles
    if response_times:
        response_times_sorted = sorted(response_times.values())
        p95_index = int(len(response_times_sorted) * 0.95)
        p99_index = int(len(response_times_sorted) * 0.99)
        p95 = response_times_sorted[min(p95_index, len(response_times_sorted)-1)]
        p99 = response_times_sorted[min(p99_index, len(response_times_sorted)-1)]
    else:
        p95 = p99 = 0

    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    # Validate thresholds
    passed = True
    if p95 > thresholds['response_time_95p']:
        print(f"FAIL: 95th percentile response time {p95}ms exceeds threshold {thresholds['response_time_95p']}ms")
        passed = False
    if p99 > thresholds['response_time_99p']:
        print(f"FAIL: 99th percentile response time {p99}ms exceeds threshold {thresholds['response_time_99p']}ms")
        passed = False
    if failure_rate > thresholds['failure_rate']:
        print(f"FAIL: Failure rate {failure_rate:.1f}% exceeds threshold {thresholds['failure_rate']}%")
        passed = False

    if passed:
        print("SUCCESS: All performance thresholds met!")
    else:
        print("FAILURE: Performance thresholds not met!")

    # Print summary
    print(f"\nLoad Test Summary ({ENVIRONMENT} environment):")
    print(f"Total Requests: {total_requests}")
    print(f"Total Failures: {total_failures}")
    print(f"Failure Rate: {failure_rate:.1f}%")
    print(f"95th Percentile Response Time: {p95}ms")
    print(f"99th Percentile Response Time: {p99}ms")

class MyCFAToolUser(HttpUser):
    """
    Locust user class for load testing MyCFATool dashboard.
    Simulates realistic user interactions with the Dash application.
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    host = env_config['host']  # Set host from config

    def on_start(self):
        """Setup when user starts - load main page and optionally login"""
        # Load main page first
        self.client.get("/")
        # Simulate authentication if required
        self.login()

    def login(self):
        """Simulate user login using random test user"""
        test_user = random.choice(TEST_USERS)

        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "auth-msg.children",
                "inputs": [
                    {"id": "login-btn", "property": "n_clicks", "value": 1}
                ],
                "state": [
                    {"id": "username-input", "property": "value", "value": test_user['username']},
                    {"id": "password-input", "property": "value", "value": test_user['password']}
                ],
                "changedPropIds": ["login-btn.n_clicks"]
            },
            headers={"Content-Type": "application/json"},
            name="login",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Login failed with status {response.status_code}")

    @task(3)  # Higher weight for overview browsing
    def browse_overview(self):
        """Simulate browsing the overview page"""
        # Navigate to overview
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "page-content.children",
                "inputs": [
                    {"id": "url", "property": "pathname", "value": "/"}
                ],
                "state": [],
                "changedPropIds": ["url.pathname"]
            },
            headers={"Content-Type": "application/json"},
            name="navigate_overview",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Navigation failed: {response.status_code}")

        # Select random ticker and load data
        ticker = random.choice(SAMPLE_TICKERS)
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": ["overview-chart.figure", "overview-table.children"],
                "inputs": [
                    {"id": "ticker-dropdown", "property": "value", "value": ticker},
                    {"id": "period-dropdown", "property": "value", "value": "annual"}
                ],
                "state": [],
                "changedPropIds": ["ticker-dropdown.value"]
            },
            headers={"Content-Type": "application/json"},
            name="load_overview_data",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Data loading failed: {response.status_code}")

    @task(2)
    def view_financial_statements(self):
        """Simulate viewing financial statements"""
        # Navigate to financial statements
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "page-content.children",
                "inputs": [
                    {"id": "url", "property": "pathname", "value": "/financial_statements"}
                ],
                "state": [],
                "changedPropIds": ["url.pathname"]
            },
            headers={"Content-Type": "application/json"},
            name="navigate_financial_statements",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Navigation failed: {response.status_code}")

        # Load financial data for random ticker
        ticker = random.choice(SAMPLE_TICKERS)
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": ["income-table.children", "balance-table.children", "cash-table.children"],
                "inputs": [
                    {"id": "fs-ticker-dropdown", "property": "value", "value": ticker},
                    {"id": "fs-period-dropdown", "property": "value", "value": "annual"}
                ],
                "state": [],
                "changedPropIds": ["fs-ticker-dropdown.value"]
            },
            headers={"Content-Type": "application/json"},
            name="load_financial_statements",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Financial data loading failed: {response.status_code}")

    @task(1)
    def perform_technical_analysis(self):
        """Simulate technical analysis viewing"""
        # Navigate to technicals
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "page-content.children",
                "inputs": [
                    {"id": "url", "property": "pathname", "value": "/technicals"}
                ],
                "state": [],
                "changedPropIds": ["url.pathname"]
            },
            headers={"Content-Type": "application/json"},
            name="navigate_technicals",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Navigation failed: {response.status_code}")

        # Load technical analysis for random ticker
        ticker = random.choice(SAMPLE_TICKERS)
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": ["tech-main-chart.figure", "tech-table.children"],
                "inputs": [
                    {"id": "tech-ticker-dropdown", "property": "value", "value": ticker},
                    {"id": "tech-period-dropdown", "property": "value", "value": "daily"}
                ],
                "state": [
                    {"id": "tech-indicator-checklist", "property": "value", "value": ["sma", "rsi", "macd"]}
                ],
                "changedPropIds": ["tech-ticker-dropdown.value"]
            },
            headers={"Content-Type": "application/json"},
            name="load_technical_analysis",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Technical analysis failed: {response.status_code}")

    @task(1)
    def create_portfolio(self):
        """Simulate portfolio creation"""
        # Navigate to portfolio
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "page-content.children",
                "inputs": [
                    {"id": "url", "property": "pathname", "value": "/portfolio"}
                ],
                "state": [],
                "changedPropIds": ["url.pathname"]
            },
            headers={"Content-Type": "application/json"},
            name="navigate_portfolio",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Navigation failed: {response.status_code}")

        # Select multiple tickers and create portfolio
        selected_tickers = random.sample(SAMPLE_TICKERS, 3)  # Select 3 random tickers
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": ["portfolio-summary-table.children", "portfolio-pie-chart.figure", "portfolio-performance-chart.figure"],
                "inputs": [
                    {"id": "create-portfolio-btn", "property": "n_clicks", "value": 1}
                ],
                "state": [
                    {"id": "portfolio-ticker-dropdown", "property": "value", "value": selected_tickers}
                ],
                "changedPropIds": ["create-portfolio-btn.n_clicks"]
            },
            headers={"Content-Type": "application/json"},
            name="create_portfolio_analysis",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Portfolio creation failed: {response.status_code}")

    @task(1)
    def generate_pdf_report(self):
        """Simulate PDF report generation"""
        ticker = random.choice(SAMPLE_TICKERS)
        # Export overview PDF
        with self.client.post(
            "/_dash-update-component",
            json={
                "output": "overview-export-msg.children",
                "inputs": [
                    {"id": "overview-export-btn", "property": "n_clicks", "value": 1}
                ],
                "state": [
                    {"id": "ticker-dropdown", "property": "value", "value": ticker},
                    {"id": "period-dropdown", "property": "value", "value": "annual"}
                ],
                "changedPropIds": ["overview-export-btn.n_clicks"]
            },
            headers={"Content-Type": "application/json"},
            name="generate_pdf_report",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"PDF generation failed: {response.status_code}")


class LightUser(MyCFAToolUser):
    """Light browsing user - mostly views overview and basic data"""
    wait_time = between(2, 8)

    @task(5)
    def browse_overview(self):
        super().browse_overview()

    @task(1)
    def view_financial_statements(self):
        super().view_financial_statements()


class HeavyUser(MyCFAToolUser):
    """Heavy analysis user - performs deep analysis and generates reports"""
    wait_time = between(1, 3)

    @task(2)
    def perform_technical_analysis(self):
        super().perform_technical_analysis()

    @task(2)
    def create_portfolio(self):
        super().create_portfolio()

    @task(2)
    def generate_pdf_report(self):
        super().generate_pdf_report()


class MixedUser(MyCFAToolUser):
    """Mixed usage user - combination of browsing and analysis"""
    wait_time = between(1, 5)

    # Inherits all tasks with default weights