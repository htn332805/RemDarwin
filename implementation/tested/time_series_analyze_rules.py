import pandas as pd
import sys

def evaluate_rules(df):
    results = {}

    # Ensure data is sorted by date
    df = df.sort_values('date').copy()

    # Growth Trend Rules
    # Rule 1: Average YoY growth in revenue > 10%
    df['revenue_yoy'] = df['revenue'].pct_change()
    avg_rev_yoy = df['revenue_yoy'].dropna().mean() * 100
    results['Revenue YoY Growth > 10%'] = {
        'met': avg_rev_yoy > 10,
        'evidence': f'Average YoY growth: {avg_rev_yoy:.2f}%'
    }

    # Rule 2: CAGR of revenue > 20%
    first_rev = df['revenue'].iloc[0]
    last_rev = df['revenue'].iloc[-1]
    n = len(df) - 1
    cagr_rev = (last_rev / first_rev)**(1/n) - 1 if first_rev != 0 else 0
    cagr_rev_pct = cagr_rev * 100
    results['Revenue CAGR > 20%'] = {
        'met': cagr_rev_pct > 20,
        'evidence': f'CAGR: {cagr_rev_pct:.2f}%'
    }

    # Rule 3: Average YoY growth in netIncome > 5%
    df['netIncome_yoy'] = df['netIncome'].pct_change()
    avg_net_yoy = df['netIncome_yoy'].dropna().mean() * 100
    results['Net Income YoY Growth > 5%'] = {
        'met': avg_net_yoy > 5,
        'evidence': f'Average YoY growth: {avg_net_yoy:.2f}%'
    }

    # Rule 4: Momentum - last 3 years avg YoY revenue > previous 3 years avg
    if len(df) >= 6:
        last3_rev_yoy = df['revenue_yoy'].tail(3).mean()
        prev3_rev_yoy = df['revenue_yoy'].iloc[-6:-3].mean()
        results['Revenue Momentum'] = {
            'met': last3_rev_yoy > prev3_rev_yoy,
            'evidence': f'Last 3 avg: {last3_rev_yoy:.4f}, Prev 3 avg: {prev3_rev_yoy:.4f}'
        }
    else:
        results['Revenue Momentum'] = {
            'met': False,
            'evidence': 'Not enough data'
        }

    # Profitability Threshold Rules
    # Rule 1: Average net profit margin > 10%
    df['margin'] = df['netIncome'] / df['revenue']
    avg_margin = df['margin'].dropna().mean() * 100
    results['Average Net Margin > 10%'] = {
        'met': avg_margin > 10,
        'evidence': f'Average margin: {avg_margin:.2f}%'
    }

    # Rule 2: Margin consistency - variance of margins < 0.05
    var_margin = df['margin'].dropna().var()
    results['Margin Consistency'] = {
        'met': var_margin < 0.05,
        'evidence': f'Variance: {var_margin:.4f}'
    }

    # Rule 3: Stability - no negative netIncome in last 5 years
    last5_neg = (df['netIncome'].tail(5) < 0).any()
    results['Net Income Stability'] = {
        'met': not last5_neg,
        'evidence': 'All positive in last 5 years' if not last5_neg else 'Negative in last 5 years'
    }

    # Cash Flow Stability Rules
    # Rule 1: Positivity - all freeCashFlow > 0
    all_pos_fcf = (df['freeCashFlow'].dropna() > 0).all()
    results['FCF Positivity'] = {
        'met': all_pos_fcf,
        'evidence': 'All FCF positive' if all_pos_fcf else 'Some negative FCF'
    }

    # Rule 2: Coverage - average FCF / netIncome > 0.5
    df['fcf_coverage'] = df['freeCashFlow'] / df['netIncome']
    avg_coverage = df['fcf_coverage'].dropna().mean()
    results['FCF Coverage > 0.5'] = {
        'met': avg_coverage > 0.5,
        'evidence': f'Average coverage: {avg_coverage:.2f}'
    }

    # Rule 3: Volatility - variance of FCF YoY growth < 0.5
    df['fcf_yoy'] = df['freeCashFlow'].pct_change()
    var_fcf_yoy = df['fcf_yoy'].dropna().var()
    results['FCF Volatility'] = {
        'met': var_fcf_yoy < 0.5,
        'evidence': f'Variance: {var_fcf_yoy:.4f}'
    }

    # Rule 4: Trends - freeCashFlow is monotonically increasing
    increasing_fcf = df['freeCashFlow'].dropna().is_monotonic_increasing
    results['FCF Increasing Trend'] = {
        'met': increasing_fcf,
        'evidence': 'Monotonically increasing' if increasing_fcf else 'Not monotonically increasing'
    }

    # Risk Signal Rules
    # Rule 1: Negatives - number of negative netIncome years < 2
    neg_years = (df['netIncome'] < 0).sum()
    results['Few Negative Years'] = {
        'met': neg_years < 2,
        'evidence': f'Negative years: {neg_years}'
    }

    # Rule 2: Declines - no 3 consecutive revenue declines
    consecutive_decline = False
    for i in range(2, len(df)):
        if df['revenue'].iloc[i] < df['revenue'].iloc[i-1] < df['revenue'].iloc[i-2]:
            consecutive_decline = True
            break
    results['No 3 Consecutive Declines'] = {
        'met': not consecutive_decline,
        'evidence': 'No 3 consecutive declines' if not consecutive_decline else 'Has 3 consecutive declines'
    }

    # Rule 3: Volatility - variance of revenue YoY growth < 0.3
    var_rev_yoy = df['revenue_yoy'].dropna().var()
    results['Revenue Volatility'] = {
        'met': var_rev_yoy < 0.3,
        'evidence': f'Variance: {var_rev_yoy:.4f}'
    }

    # Rule 4: Reversals - no sudden drop > 50% in revenue
    sudden_drop = False
    for i in range(1, len(df)):
        if df['revenue'].iloc[i] / df['revenue'].iloc[i-1] < 0.5:
            sudden_drop = True
            break
    results['No Sudden Drops'] = {
        'met': not sudden_drop,
        'evidence': 'No sudden drops >50%' if not sudden_drop else 'Has sudden drop >50%'
    }

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_rules.py <ticker>")
        sys.exit(1)
    ticker = sys.argv[1]
    file_path = f'data/{ticker}_combined_time_series.csv'
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    results = evaluate_rules(df)
    for rule, res in results.items():
        print(f"{rule}: {'Met' if res['met'] else 'Not Met'} - {res['evidence']}")