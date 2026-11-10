# Subscription Analytics System

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-database-003B57?logo=sqlite&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-analysis-150458?logo=pandas&logoColor=white)

A SQL-driven analytics project for a subscription-based service. It generates a realistic synthetic dataset in SQLite and answers three common business questions with SQL: **who is paying but not using the product, who is about to churn, and who are the most valuable customers.**

---

## Business Questions

| # | Question | Technique |
|---|----------|-----------|
| 1 | **Inactive paying users** — active subscribers with zero usage in the last 30 days | Conditional aggregation, `LEFT JOIN`, `HAVING` |
| 2 | **Churn candidates** — users whose usage dropped by **80%+** compared to the previous two weeks | CTE (`WITH`), period-over-period comparison |
| 3 | **Customer Lifetime Value (LTV)** — monthly price × subscription length | Date arithmetic with `julianday`, `COALESCE` for active subscriptions |

## Data Model

```
users ─────────┬──< subscriptions >── plans
  user_id      │      user_id            plan_id
  name         │      plan_id            plan_name
  email        │      start_date         monthly_price
  signup_date  │      end_date
  country      │      status (active / cancelled)
               │
               └──< usage_logs
                      user_id
                      usage_date
                      minutes_used
```

## Synthetic Data

| Table | Rows | Details |
|-------|------|---------|
| `plans` | 3 | Basic (100), Standard (150), Premium (250) |
| `users` | 200 | Turkey, Germany, USA, France |
| `subscriptions` | 200 | ~20% cancelled |
| `usage_logs` | 12,000 | 60 days of daily usage per user |

Users are assigned behaviour profiles so the analyses return meaningful results:

- **~10% inactive** — no usage in the last 30 days
- **~15% declining** — usage collapses in the last 14 days (churn signal)
- **the rest** — normal, varied daily usage

A fixed random seed (`42`) keeps the dataset reproducible.

---

## Getting Started

```bash
git clone https://github.com/Sevvalgungorr/subscription-analytics-system.git
cd subscription-analytics-system
pip install -r requirements.txt
python main.py
```

The script recreates `subscription.db` on every run, so the database file is not tracked in the repository.

## Example Output

```
Aktif ama kullanmayan kullanıcı sayısı:
16

Churn adayı sayısı:
27

En değerli 10 kullanıcı:
     user_id  monthly_price     months          LTV
186      187          250.0  12.100000  3025.000000
93        94          250.0  11.400000  2850.000000
...

En riskli 10 kullanıcı:
    user_id  last14  prev14  drop_ratio
7        63      12     855    0.985965
18      144      12     661    0.981846
...
```

*Exact numbers vary slightly because dates are calculated relative to the day the script runs.*

---

## Possible Improvements

- [ ] Export results to CSV / Excel
- [ ] Visualise churn and LTV distributions with matplotlib
- [ ] Segment LTV by country and plan
- [ ] Move SQL queries into separate `.sql` files

## Author

**Şevval Güngör** — Computer Engineering, Kırıkkale University
