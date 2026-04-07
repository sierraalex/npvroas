import duckdb
import os
import pandas as pd

pd.options.display.float_format = '{:,.0f}'.format

base_dir = os.path.dirname(os.path.abspath(__file__))
outputs_dir = os.path.join(base_dir, "outputs")

con = duckdb.connect(database='marketing.duckdb', read_only=False)

# Load CSVs into DuckDB tables
con.execute(f"CREATE OR REPLACE TABLE spend AS SELECT * FROM read_csv_auto('{outputs_dir}/spend.csv')")
con.execute(f"CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('{outputs_dir}/customers.csv')")
con.execute(f"CREATE OR REPLACE TABLE cashflows AS SELECT * FROM read_csv_auto('{outputs_dir}/cashflows.csv')")
con.execute(f"CREATE OR REPLACE TABLE channel_metrics AS SELECT * FROM read_csv_auto('{outputs_dir}/channel_metrics.csv')")
con.execute(f"CREATE OR REPLACE TABLE diagnostics AS SELECT * FROM read_csv_auto('{outputs_dir}/diagnostics.csv')")
con.execute(f"CREATE OR REPLACE TABLE final_channel_ranking AS SELECT * FROM read_csv_auto('{outputs_dir}/final_channel_ranking.csv')")

# Query 1: NPV per dollar by channel
result_1 = con.execute("""
SELECT
    channel,
    SUM(total_npv) / SUM(total_spend) AS npv_per_dollar
FROM channel_metrics
GROUP BY channel
ORDER BY npv_per_dollar DESC
""").fetchdf()

print("\nNPV per dollar by channel:")
print(result_1)

# Query 2: Customers and total NPV by channel
result_2 = con.execute("""
SELECT
    c.channel,
    COUNT(DISTINCT c.customer_id) AS customers,
    SUM(f.npv_margin) AS total_npv
FROM customers c
JOIN cashflows f
    ON c.customer_id = f.customer_id
GROUP BY c.channel
ORDER BY total_npv DESC
""").fetchdf()

print("\nCustomers and total NPV by channel:")
print(result_2)