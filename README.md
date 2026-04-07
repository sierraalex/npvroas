# NPVROAS — Marketing as Capital Allocation

A framework for evaluating marketing spend using NPV, marginal analysis, and cashflow modeling instead of ROAS.

"A junior marketer worries about ROAS. A better marketer worries about ROI. A serious capital allocator thinks in NPV."

---

## Why this exists

Most marketing decisions optimize average performance metrics:
- ROAS  
- ROI  
- LTV:CAC  

None of these answer the real question:

Where should the next dollar go?

---

## Core idea

NPVROAS treats marketing like capital deployment:

NPVROAS = NPV(customer cashflows) / marketing investment

Instead of measuring:
Revenue / Spend

We model:
- time value of money  
- churn and retention  
- expansion revenue  
- saturation (diminishing returns)  
- marginal returns by channel  

---

## Key insight

The channels with the best average returns are often the worst place to allocate the next dollar.

Because they are already saturated.

Meanwhile, “worse” channels can generate higher marginal NPV when they are still on the steep part of their response curve.

This is the same logic used in corporate finance — but rarely applied to marketing.

---

## What’s in this repo

- Python simulation of a SaaS-style marketing system  
- Adstock + response curve modeling  
- Customer-level cashflow generation (36-month horizon)  
- NPV calculation with discounting  
- Marginal budget allocation via simulation  
- Visualization comparing ROAS vs NPV  

---

## Visuals

- Video walkthrough: /media/roas_vs_npv.mov  
- Formula map: /visualizations/formula_map.html  

---

## Model components

Media layer  
- Adstock (channel-specific decay)  
- Log + Hill response curves  
- Seasonality  

Customer layer  
- Personas (Enterprise, Mid-Market, SMB, Startup)  
- Retention / churn  
- Expansion revenue  
- Sales cycle delay  

Finance layer  
- Discounted cashflows (36 months)  
- Gross margin assumptions  
- CAC (fully loaded)  

Decision layer  
- Marginal NPV per channel  
- Budget reallocation scenarios  
- Monte Carlo simulation  

---

## Example insight

Channel performance (illustrative):

- Account-Based Marketing → highest average return, near-zero marginal gain  
- LinkedIn Ads → lower average return, highest marginal NPV  
- Paid Search → strong marginal efficiency  
- Display → negative marginal contribution  

Conclusion:

Average ≠ Marginal

---

## How to run

Generate data:

python generate_data.py

Run analysis:

duckdb < query_duckdb.py

---

## What this is (and is not)

This is:
- a framework for thinking about marketing allocation  
- a simulation environment  
- a bridge between marketing and finance  

This is not:
- a production MMM system  
- a replacement for experimentation  
- a fully calibrated real-world model  

---

## Why it matters

Marketing is often the largest discretionary budget in a company.

It should be evaluated with the same rigor as:
- capital expenditures  
- M&A decisions  
- portfolio allocation  

---

## Author

Alex Sierra  
Aerospace Engineering → MBA (Marketing) → MS Finance  

Working at the intersection of marketing science, finance, and decision theory

---

## License

MIT