import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# --- PARAMETERS (change these to stress-test your model) ---
START_DATE = datetime(2024, 1, 1)
MONTHS_HORIZON = 36        # LTV/NPV lookback window
DISCOUNT_RATE_ANNUAL = 0.10  # 10% — standard marketing hurdle rate
# old way NUM_CUSTOMERS = 5000       # customers acquired over the year
GROSS_MARGIN = 0.80 # 80% gross margin for SaaS (added this as a global constant for use in cashflow calculations)

# --- CHANNEL MMM PARAMETERS (change these to stress-test your model) ---
CHANNEL_MMM_PARAMS = {
    'Paid_Search': {
        'theta': 0.20,
        'response_type': 'log',
        'beta': 180,
        'k': 0.000020
    },
    'Content': {
        'theta': 0.60,
        'response_type': 'log',
        'beta': 150,
        'k': 0.000018
    },
    'Organic': {
        'theta': 0.50,
        'response_type': 'log',
        'beta': 70,
        'k': 0.000030
    },
    'LinkedIn': {
        'theta': 0.45,
        'response_type': 'log',
        'beta': 120,
        'k': 0.000016
    },
    'Display': {
        'theta': 0.30,
        'response_type': 'log',
        'beta': 90,
        'k': 0.000010
    },
    'Direct': {
        'theta': 0.10,
        'response_type': 'fixed',
        'base_customers': 60
    },
    'Account_Based': {
    'theta': 0.55,
    'response_type': 'hill',
    'beta': 300,
    'alpha': 1.25,
    'lam': 1600000
},
}


# --- PERSONA DEFINITIONS ---
PERSONAS = {
    'Enterprise_Strategic':    {'share': 0.08, 'acv': 5000, 'monthly_retention': 0.985, 'expansion_rate': 0.18, 'sales_cycle_days': 90, 'channels': ['LinkedIn', 'Direct']},
    'Mid_Market_Pragmatist':   {'share': 0.22, 'acv': 1500, 'monthly_retention': 0.955, 'expansion_rate': 0.08, 'sales_cycle_days': 35, 'channels': ['Paid_Search', 'Content']},
    'Self_Serve_Growth':       {'share': 0.40, 'acv': 500, 'monthly_retention': 0.925, 'expansion_rate': 0.01, 'sales_cycle_days': 3, 'channels': ['Paid_Search', 'Organic']},
    'Free_Trial_Churner':      {'share': 0.18, 'acv': 300, 'monthly_retention': 0.70, 'expansion_rate': 0.00, 'sales_cycle_days': 14, 'channels': ['Organic', 'Display']},
    'Enterprise_Expansion':    {'share': 0.12, 'acv': 8000, 'monthly_retention': 0.99, 'expansion_rate': 0.25, 'sales_cycle_days': 120, 'channels': ['Direct', 'Account_Based']},
}

# -- Customer Acquisition Cost (CAC) and conversion rates by channel
CHANNELS = {
    'Paid_Search': {'cac': 802, 'conversion_rate': 0.05},
    'Content': {'cac': 350, 'conversion_rate': 0.02},
    'Organic': {'cac': 250, 'conversion_rate': 0.015},
    'LinkedIn': {'cac': 982, 'conversion_rate': 0.03},
    'Display': {'cac': 400, 'conversion_rate': 0.01},
    'Direct': {'cac': 0, 'conversion_rate': 0.10},
    'Account_Based': {'cac': 1200, 'conversion_rate': 0.04},
}

SALES_COST_MULTIPLIER = {
    'Account_Based': 2.5,
    'LinkedIn': 1.8,
    'Content': 1.3,
    'Paid_Search': 1.1,
    'Organic': 1.0,
    'Display': 1.1,
    'Direct': 1.0,
}

# Formula Definitions for adstock with different response curves for each channel

def adstock_series(spend_values, theta):
    result = []
    carry = 0.0
    for s in spend_values:
        carry = s + theta * carry
        result.append(carry)
    return np.array(result)

def log_response(x, beta, k):
    return beta * np.log1p(k * x)

def hill_response(x, beta, alpha, lam):
    numerator = x ** alpha
    denominator = numerator + lam
    return beta * (numerator / denominator)

def generate_customers(num_customers, personas, channels):
    customers = []
    
    for i in range(num_customers):
        persona_name = np.random.choice(
            list(personas.keys()),
            p=[personas[p]['share'] for p in personas.keys()]
        )
        persona = personas[persona_name]
        channel = np.random.choice(persona['channels'])
        acq_date = START_DATE + timedelta(days=np.random.randint(0, 365))
        
        customers.append({
            'customer_id': i,
            'persona': persona_name,
            'channel': channel,
            'acq_date': acq_date,
            'acv': persona['acv'],
            'monthly_retention': persona['monthly_retention'],
            'expansion_rate': persona['expansion_rate'],
            'sales_cycle_days': persona['sales_cycle_days'],
        })
    
    return pd.DataFrame(customers)


# MArginal NPV framework



# replaced this fore a more realistic conncetion between Channel and CashFlows
# customers_df = generate_customers(NUM_CUSTOMERS, PERSONAS, CHANNELS)


CHANNEL_PERSONA_WEIGHTS = {}

for channel_name in CHANNELS.keys():
    eligible = {
        name: info['share']
        for name, info in PERSONAS.items()
        if channel_name in info['channels']
    }
    names = list(eligible.keys())
    probs = np.array(list(eligible.values()), dtype=float)
    probs = probs / probs.sum()
    CHANNEL_PERSONA_WEIGHTS[channel_name] = (names, probs)


def choose_persona_for_channel(channel, personas):
    names, probs = CHANNEL_PERSONA_WEIGHTS[channel]
    return np.random.choice(names, p=probs)





def generate_customers_from_spend(spend_df, personas, channels, mmm_params, start_year=2024, reference_spend_map=None):
    customers = []
    diagnostics = []
    customer_id = 0

    if reference_spend_map is None:
        reference_spend_map = (
            spend_df.groupby('channel', as_index=True)['spend']
            .mean()
            .to_dict()
        )

    channel_decay_strength = {
        'Paid_Search': 0.35,
        'Content': 0.20,
        'Organic': 0.60,
        'LinkedIn': 0.40,
        'Display': 0.75,
        'Direct': 0.00,
        'Account_Based': 0.18,
    }

    for channel in spend_df['channel'].unique():
        channel_spend = (
            spend_df[spend_df['channel'] == channel]
            .sort_values('month')
            .copy()
        )

        params = mmm_params[channel]
        spend_values = channel_spend['spend'].values
        adstocked_spend = adstock_series(spend_values, params['theta'])

        if params['response_type'] == 'fixed':
            raw_expected_customers = np.repeat(params['base_customers'], len(channel_spend))
        elif params['response_type'] == 'log':
            raw_expected_customers = log_response(
                adstocked_spend,
                params['beta'],
                params['k']
            )
        elif params['response_type'] == 'hill':
            raw_expected_customers = hill_response(
                adstocked_spend,
                params['beta'],
                params['alpha'],
                params['lam']
            )
        else:
            raise ValueError(f"Unknown response_type for channel {channel}")

        baseline_spend = reference_spend_map[channel]
        decay_strength = channel_decay_strength[channel]

        if baseline_spend <= 0:
            spend_ratio = np.ones(len(channel_spend), dtype=float)
            efficiency_multiplier = np.ones(len(channel_spend), dtype=float)
        else:
            spend_ratio = channel_spend['spend'].values / baseline_spend
            efficiency_multiplier = 1 / (
                1 + decay_strength * np.maximum(spend_ratio - 1, 0)
            )

        expected_customers_series = raw_expected_customers * efficiency_multiplier
        expected_customers_series = np.maximum(expected_customers_series, 0.0)
        expected_customers_series = np.nan_to_num(
            expected_customers_series,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        channel_spend['adstocked_spend'] = adstocked_spend
        channel_spend['raw_expected_customers'] = raw_expected_customers
        channel_spend['efficiency_multiplier'] = efficiency_multiplier
        channel_spend['expected_customers'] = expected_customers_series

        for _, row in channel_spend.iterrows():
            month = int(row['month'])
            spend = float(row['spend'])
            adstocked = float(row['adstocked_spend'])
            raw_expected = max(float(row['raw_expected_customers']), 0.0)
            efficiency_mult = float(np.nan_to_num(row['efficiency_multiplier'], nan=1.0))
            expected_customers = max(float(np.nan_to_num(row['expected_customers'], nan=0.0)), 0.0)

            lam = max(float(expected_customers), 0.0)
            if np.isnan(lam):
                lam = 0.0
            num_acquired = np.random.poisson(lam)

            diagnostics.append({
                'month': month,
                'channel': channel,
                'spend': spend,
                'adstocked_spend': adstocked,
                'raw_expected_customers': raw_expected,
                'efficiency_multiplier': efficiency_mult,
                'expected_customers': expected_customers,
                'actual_customers': num_acquired,
                'response_type': params['response_type'],
                'theta': params['theta'],
                'beta': params.get('beta', np.nan),
                'k': params.get('k', np.nan),
                'alpha': params.get('alpha', np.nan),
                'lam': params.get('lam', np.nan),
            })

            month_start = datetime(start_year, month, 1)
            if month == 12:
                next_month = datetime(start_year + 1, 1, 1)
            else:
                next_month = datetime(start_year, month + 1, 1)

            days_in_month = (next_month - month_start).days

            for _ in range(num_acquired):
                persona_name = choose_persona_for_channel(channel, personas)
                persona = personas[persona_name]

                acq_date = month_start + timedelta(days=np.random.randint(0, days_in_month))

                customers.append({
                    'customer_id': customer_id,
                    'persona': persona_name,
                    'channel': channel,
                    'acq_date': acq_date,
                    'acquisition_month': month,
                    'adstocked_spend': adstocked,
                    'expected_customers_channel_month': expected_customers,
                    'acv': persona['acv'],
                    'monthly_retention': persona['monthly_retention'],
                    'expansion_rate': persona['expansion_rate'],
                    'sales_cycle_days': persona['sales_cycle_days'],
                })

                customer_id += 1

    return pd.DataFrame(customers), pd.DataFrame(diagnostics)


def generate_cashflows(customers_df, months_horizon, discount_rate_annual):
    """Vectorized cashflow generation matching original logic:
    customer earns revenue in the churn month, then becomes inactive after."""
    monthly_discount_rate = (1 + discount_rate_annual) ** (1 / 12) - 1

    n = len(customers_df)
    months = np.arange(months_horizon)

    customer_ids = customers_df['customer_id'].values
    personas = customers_df['persona'].values
    channels_arr = customers_df['channel'].values
    acv = customers_df['acv'].values.astype(float)
    retention = customers_df['monthly_retention'].values.astype(float)
    expansion = customers_df['expansion_rate'].values.astype(float)
    conv_month = (customers_df['sales_cycle_days'].values // 30).astype(int)

    month_grid = np.broadcast_to(months, (n, months_horizon))
    conv_grid = conv_month[:, None]

    paying = month_grid >= conv_grid
    months_active = np.maximum(month_grid - conv_grid, 0)

    expanded_acv = acv[:, None] * (1 + expansion[:, None] * (months_active / 12.0))
    base_revenue = (expanded_acv / 12.0) * paying

    rng = np.random.random((n, months_horizon))
    churned_this_month = rng > retention[:, None]
    churned_this_month[~paying] = False

    churn_effective_next_month = np.roll(churned_this_month, 1, axis=1)
    churn_effective_next_month[:, 0] = False

    churned_before_month = np.maximum.accumulate(churn_effective_next_month.astype(int), axis=1)
    is_active = churned_before_month == 0

    revenue = base_revenue * is_active

    discount_factors = 1.0 / ((1.0 + monthly_discount_rate) ** months)
    npv_margin = revenue * GROSS_MARGIN * discount_factors[None, :]

    cashflows_df = pd.DataFrame({
        'customer_id': np.repeat(customer_ids, months_horizon),
        'persona': np.repeat(personas, months_horizon),
        'channel': np.repeat(channels_arr, months_horizon),
        'month': np.tile(months, n),
        'revenue': revenue.ravel(),
        'npv_margin': npv_margin.ravel(),
        'is_active': is_active.ravel(),
    })

    return cashflows_df

def generate_marketing_spend(months=12, channels=CHANNELS):
    """Generate monthly marketing spend by channel with seasonality."""
    spend_data = []
    
    # Seasonality multipliers by month
    seasonality = {
        1: 1.0, 2: 1.0, 3: 1.0,      # Jan-Mar: baseline
        4: 0.8, 5: 0.8, 6: 0.8,      # Apr-Jun: -20%
        7: 0.6, 8: 0.6,               # Jul-Aug: -40%
        9: 1.5, 10: 1.5, 11: 1.5,    # Sep-Nov: +50%
        12: 1.8                        # Dec: +80%
    }
    
    # Base monthly spend by channel

    base_spend = {
    'Paid_Search': 300000,
    'Content': 120000,
    'Organic': 40000,
    'LinkedIn': 250000,
    'Display': 100000,
    'Direct': 0,
    'Account_Based': 400000,
    }
    
    for month in range(1, months + 1):
        for channel, base in base_spend.items():
            seasonal_spend = base * seasonality[month]
            spend_data.append({
                'month': month,
                'channel': channel,
                'spend': seasonal_spend,
            })
    
    return pd.DataFrame(spend_data)

def reallocate_budget(spend_df):
    new_spend_df = spend_df.copy()

    # take 60% of Display spend
    display_mask = new_spend_df['channel'] == 'Display'
    display_cut = new_spend_df.loc[display_mask, 'spend'] * 0.60

    # reduce Display
    new_spend_df.loc[display_mask, 'spend'] *= 0.40

    # redistribute
    new_spend_df.loc[new_spend_df['channel'] == 'Account_Based', 'spend'] += display_cut.values * 0.70
    new_spend_df.loc[new_spend_df['channel'] == 'LinkedIn', 'spend'] += display_cut.values * 0.30

    return new_spend_df


def get_incremental_npv(spend_df, channel, delta_spend_annual, personas, channels, mmm_params,
                        months_horizon, discount_rate_annual, seed=42, n_sims=10):
    baseline_npvs = []
    test_npvs = []

    reference_spend_map = spend_df.groupby('channel')['spend'].mean().to_dict()
    delta_spend_monthly = delta_spend_annual / 12.0

    for sim in range(n_sims):
        np.random.seed(seed + sim)

        baseline_customers_df, _ = generate_customers_from_spend(
            spend_df,
            personas,
            channels,
            mmm_params,
            reference_spend_map=reference_spend_map
        )
        baseline_cashflows_df = generate_cashflows(
            baseline_customers_df, months_horizon, discount_rate_annual
        )
        baseline_total_npv = baseline_cashflows_df['npv_margin'].sum()
        baseline_npvs.append(baseline_total_npv)

        np.random.seed(seed + sim)

        test_spend_df = spend_df.copy()
        test_spend_df.loc[test_spend_df['channel'] == channel, 'spend'] += delta_spend_monthly

        test_customers_df, _ = generate_customers_from_spend(
            test_spend_df,
            personas,
            channels,
            mmm_params,
            reference_spend_map=reference_spend_map
        )
        test_cashflows_df = generate_cashflows(
            test_customers_df, months_horizon, discount_rate_annual
        )
        test_total_npv = test_cashflows_df['npv_margin'].sum()
        test_npvs.append(test_total_npv)

    avg_baseline_npv = np.mean(baseline_npvs)
    avg_test_npv = np.mean(test_npvs)

    incremental_margin_npv = avg_test_npv - avg_baseline_npv
    incremental_npv_after_spend = incremental_margin_npv - delta_spend_annual

    return incremental_npv_after_spend, avg_baseline_npv, avg_test_npv

print(" ")
print("Im coming to you!!!")



# --- MAIN EXECUTION ---
spend_df = generate_marketing_spend(months=12, channels=CHANNELS)
reference_spend_map = spend_df.groupby('channel')['spend'].mean().to_dict()

customers_df, diagnostics_df = generate_customers_from_spend(
    spend_df, PERSONAS, CHANNELS, CHANNEL_MMM_PARAMS, reference_spend_map=reference_spend_map
)

cashflows_df = generate_cashflows(customers_df, MONTHS_HORIZON, DISCOUNT_RATE_ANNUAL)

print("\nSpend sample:")
print(spend_df.head(12))

print("\nCustomer sample:")
print(customers_df.head(10))
print(f"\nTotal customers acquired: {len(customers_df)}")

print("\nCashflow sample:")
print(cashflows_df.head(20))
print("\nMargin check:")
print(cashflows_df[['revenue', 'npv_margin']].head(5))
print(f"\nTotal cashflow records: {len(cashflows_df)}")
print("\nBaseline diagnostics sample:")
print(diagnostics_df.head(12))
# --- CHANNEL ECONOMICS ---

channel_metrics = pd.DataFrame({
    'total_spend': spend_df.groupby('channel')['spend'].sum(),
    'num_customers': customers_df.groupby('channel')['customer_id'].count(),
    'total_npv': cashflows_df.groupby('channel')['npv_margin'].sum(),
})

channel_metrics['realized_cac'] = channel_metrics['total_spend'] / channel_metrics['num_customers']
channel_metrics['npv_per_customer'] = channel_metrics['total_npv'] / channel_metrics['num_customers']

channel_metrics['ltv_cac_ratio'] = np.where(
    channel_metrics['total_spend'] > 0,
    channel_metrics['total_npv'] / channel_metrics['total_spend'],
    np.nan
)

channel_metrics = channel_metrics.sort_values('ltv_cac_ratio', ascending=False)

channel_metrics['adjusted_cac'] = channel_metrics.index.map(
    lambda ch: channel_metrics.loc[ch, 'realized_cac'] * SALES_COST_MULTIPLIER[ch]
)

channel_metrics['adjusted_ltv_cac'] = channel_metrics['npv_per_customer'] / channel_metrics['adjusted_cac']

channel_metrics['payback_months'] = channel_metrics['adjusted_cac'] / (channel_metrics['npv_per_customer'] / MONTHS_HORIZON)

print("\nChannel Performance:")
print(channel_metrics)

paid_only = channel_metrics[channel_metrics.index != 'Direct']

paid_spend = paid_only['total_spend'].sum()
paid_npv = paid_only['total_npv'].sum()

print("\nPaid-media-only NPV / Spend:")
print(paid_npv / paid_spend)

# --- SANITY CHECK ---
total_spend = spend_df['spend'].sum()
total_npv = cashflows_df['npv_margin'].sum()

print("\nBlended NPV / Spend:")
print(total_npv / total_spend)

channel_metrics_no_direct = channel_metrics[channel_metrics.index != 'Direct']
print("\nChannel Performance (ex Direct):")
print(channel_metrics_no_direct)

print("\n--- REALLOCATION SCENARIO ---")

# apply new budget
reallocated_spend_df = reallocate_budget(spend_df)

# rerun pipeline
reallocated_customers_df, reallocated_diagnostics_df = generate_customers_from_spend(
    reallocated_spend_df, PERSONAS, CHANNELS, CHANNEL_MMM_PARAMS, reference_spend_map=reference_spend_map
)
reallocated_cashflows_df = generate_cashflows(
    reallocated_customers_df, MONTHS_HORIZON, DISCOUNT_RATE_ANNUAL
)

# aggregate results
reallocated_channel_metrics = pd.DataFrame({
    'total_spend': reallocated_spend_df.groupby('channel')['spend'].sum(),
    'num_customers': reallocated_customers_df.groupby('channel')['customer_id'].count(),
    'total_npv': reallocated_cashflows_df.groupby('channel')['npv_margin'].sum(),
})

# compute metrics
reallocated_channel_metrics['realized_cac'] = reallocated_channel_metrics['total_spend'] / reallocated_channel_metrics['num_customers']
reallocated_channel_metrics['npv_per_customer'] = reallocated_channel_metrics['total_npv'] / reallocated_channel_metrics['num_customers']

reallocated_channel_metrics['adjusted_cac'] = reallocated_channel_metrics.index.map(
    lambda ch: reallocated_channel_metrics.loc[ch, 'realized_cac'] * SALES_COST_MULTIPLIER[ch]
)

reallocated_channel_metrics['adjusted_ltv_cac'] = (
    reallocated_channel_metrics['npv_per_customer'] / reallocated_channel_metrics['adjusted_cac']
)
# !!!!!! OUTPUTS HERE!!!!!!!!!
# totals
baseline_total_npv = cashflows_df['npv_margin'].sum()
reallocated_total_npv = reallocated_cashflows_df['npv_margin'].sum()

print("\nBaseline total NPV margin:")
print(baseline_total_npv)

print("\nReallocated total NPV margin:")
print(reallocated_total_npv)

print("\nIncremental NPV margin:")
print(reallocated_total_npv - baseline_total_npv)

print("\nReallocated Channel Performance:")
print(reallocated_channel_metrics.sort_values('adjusted_ltv_cac', ascending=False))

print("\n--- MARGINAL NPV TEST (+$50,000 ANNUAL per channel, net of spend) ---")

print("\nDiagnostics (efficiency check):")
print(
    diagnostics_df.groupby('channel')[['raw_expected_customers', 'expected_customers', 'actual_customers']]
    .mean()
    .sort_values('expected_customers', ascending=False)
)

for ch in CHANNELS.keys():
    if ch == 'Direct':
        continue

    incremental_npv, avg_baseline_npv, avg_test_npv = get_incremental_npv(
        spend_df,
        ch,
        50000,
        PERSONAS,
        CHANNELS,
        CHANNEL_MMM_PARAMS,
        MONTHS_HORIZON,
        DISCOUNT_RATE_ANNUAL,
        seed=42,
        n_sims=10
    )

    print(f"{ch}: incremental NPV from +$50,000 spend = {incremental_npv:,.2f}")

# Save CSVs for use in Tableau BigQuery or other tools

import os

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

os.makedirs(output_dir, exist_ok=True)

spend_df.to_csv(os.path.join(output_dir, "spend.csv"), index=False)
customers_df.to_csv(os.path.join(output_dir, "customers.csv"), index=False)
cashflows_df.to_csv(os.path.join(output_dir, "cashflows.csv"), index=False)
channel_metrics.to_csv(os.path.join(output_dir, "channel_metrics.csv"))
diagnostics_df.to_csv(os.path.join(output_dir, "diagnostics.csv"), index=False)

reallocated_spend_df.to_csv(os.path.join(output_dir, "reallocated_spend.csv"), index=False)
reallocated_customers_df.to_csv(os.path.join(output_dir, "reallocated_customers.csv"), index=False)
reallocated_cashflows_df.to_csv(os.path.join(output_dir, "reallocated_cashflows.csv"), index=False)
reallocated_channel_metrics.to_csv(os.path.join(output_dir, "reallocated_channel_metrics.csv"))
reallocated_diagnostics_df.to_csv(os.path.join(output_dir, "reallocated_diagnostics.csv"), index=False)

print(f"CSV files saved to: {output_dir}")

print("\nCSV files saved.")


