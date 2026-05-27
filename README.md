# Olist E-Commerce Analytics Pipeline

> **End-to-End Data Engineering & BI Project**  
> Python · PostgreSQL · Power BI · Kaggle API · Star Schema · Kimball Methodology

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Quick Start](#4-quick-start)
5. [Environment Configuration](#5-environment-configuration)
6. [Kaggle API Setup](#6-kaggle-api-setup)
7. [Database Setup](#7-database-setup)
8. [Execution Order](#8-execution-order)
9. [Star Schema Design](#9-star-schema-design)
10. [Power BI Dashboard Overview](#10-power-bi-dashboard-overview)
11. [Key Insights](#11-key-insights)
12. [Testing](#12-testing)
13. [Project Standards](#13-project-standards)

---

## 1. Project Overview

This project delivers a **production-quality analytics engineering solution** on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — a real-world dataset covering ~99,000 orders placed between 2016–2018.

### What It Does

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Ingestion** | Kaggle API + Python | Automated dataset download & validation |
| **Transformation** | Pandas + NumPy | Cleaning, enrichment, validation |
| **Storage** | PostgreSQL | Staging + star schema |
| **Modelling** | SQL (Kimball) | Dimensions, facts, business views |
| **BI** | Power BI | Executive dashboards |
| **Testing** | pytest | Unit tests for all transformations |

### Business Questions Answered

- What is our monthly and quarterly revenue trend?
- Which product categories drive the most GMV?
- Which Brazilian states have the highest order volume and AOV?
- What percentage of deliveries arrive on time?
- Who are our most valuable customer segments?

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                             │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │  Kaggle API  │───▶│ data/raw/    │───▶│ src/transform/    │  │
│  │  (download)  │    │  CSV files   │    │ (cleaning, enrich) │  │
│  └──────────────┘    └──────────────┘    └────────┬──────────┘  │
│                                                    │              │
│                                          ┌─────────▼──────────┐  │
│                                          │ data/processed/    │  │
│                                          │  validated CSVs    │  │
│                                          └─────────┬──────────┘  │
│                                                    │              │
│                                          ┌─────────▼──────────┐  │
│                                          │  PostgreSQL         │  │
│                                          │  ├─ Staging layer  │  │
│                                          │  ├─ Dimensions      │  │
│                                          │  ├─ Fact tables     │  │
│                                          │  └─ Business views  │  │
│                                          └─────────┬──────────┘  │
│                                                    │              │
│                                          ┌─────────▼──────────┐  │
│                                          │  Power BI           │  │
│                                          │  (DirectQuery/      │  │
│                                          │   Import mode)      │  │
│                                          └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Repository Structure

```
olist_project/
│
├── data/
│   ├── raw/                        # Downloaded from Kaggle (gitignored)
│   └── processed/                  # Validated outputs (gitignored)
│
├── docs/
│   ├── data_understanding.md       # Table schemas, relationships, ERD
│   ├── data_quality_report.md      # Null counts, duplicate analysis, validation
│   └── insights_summary.md         # Business findings & recommendations
│
├── sql/
│   ├── staging/
│   │   └── create_staging_tables.sql
│   ├── dimensions/
│   │   ├── dim_date.sql
│   │   └── dim_customers_products.sql
│   ├── facts/
│   │   └── fact_orders.sql
│   ├── validation/
│   │   └── validate_all.sql
│   └── views/
│       └── business_views.sql
│
├── src/
│   ├── ingest/
│   │   └── 00_download_dataset.py   # Kaggle API download
│   ├── transform/
│   │   ├── customers_cleaning.py
│   │   ├── products_cleaning.py
│   │   ├── orders_cleaning.py
│   │   └── revenue_enrichment.py
│   ├── utils/
│   │   ├── config.py               # All paths & constants
│   │   ├── file_utils.py           # CSV I/O, ZIP extraction
│   │   ├── validation_utils.py     # Reusable validation functions
│   │   └── logging_utils.py        # Centralised logging factory
│   └── load/
│       └── load_to_sql.py          # CSV → PostgreSQL staging
│
├── tests/
│   └── test_transformations.py     # pytest unit tests
│
├── dashboards/
│   └── olist_dashboard.pbix        # Power BI file
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 4. Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running locally or accessible remotely)
- Power BI Desktop (Windows; for dashboard)
- Kaggle account with API key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/olist-analytics.git
cd olist-analytics

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (see Section 5)
cp .env.example .env
# Edit .env with your credentials

# 5. Run the full pipeline (see Section 8 for individual steps)
python -m src.ingest.00_download_dataset
python -m src.transform.customers_cleaning
python -m src.transform.products_cleaning
python -m src.transform.orders_cleaning
python -m src.transform.revenue_enrichment
python -m src.load.load_to_sql
```

---

## 5. Environment Configuration

Create a `.env` file in the project root (this file is gitignored):

```env
# ── Kaggle ─────────────────────────────────
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key

# ── Database ───────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_NAME=olist_db
DB_USER=postgres
DB_PASSWORD=your_db_password

# ── Logging ────────────────────────────────
LOG_LEVEL=INFO
```

Load environment variables before running:

```bash
# macOS/Linux
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object { $var = $_.Split('='); [System.Environment]::SetEnvironmentVariable($var[0], $var[1]) }
```

> ⚠️ **Never commit `.env` to version control.**

---

## 6. Kaggle API Setup

1. Log in to [kaggle.com](https://www.kaggle.com)
2. Go to **Account → Settings → API → Create New Token**
3. Download `kaggle.json`
4. Place it at `~/.kaggle/kaggle.json`
5. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

**Alternatively**, set environment variables directly:

```bash
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_api_key
```

The download script will automatically detect credentials from either location.

---

## 7. Database Setup

### Create Database

```sql
-- Connect as superuser and run:
CREATE DATABASE olist_db;
CREATE USER olist_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE olist_db TO olist_user;
```

### Build Schema

Execute SQL scripts in this order:

```bash
# Using psql
psql -U olist_user -d olist_db -f sql/staging/create_staging_tables.sql
# (Python loader handles staging data population)

psql -U olist_user -d olist_db -f sql/dimensions/dim_date.sql
psql -U olist_user -d olist_db -f sql/dimensions/dim_customers_products.sql
psql -U olist_user -d olist_db -f sql/facts/fact_orders.sql
psql -U olist_user -d olist_db -f sql/views/business_views.sql

# Validate
psql -U olist_user -d olist_db -f sql/validation/validate_all.sql
```

---

## 8. Execution Order

Run steps in sequence. Each step is independently executable and idempotent.

| Step | Script | Description |
|------|--------|-------------|
| 1 | `src/ingest/00_download_dataset.py` | Download & validate raw CSVs from Kaggle |
| 2 | `src/transform/customers_cleaning.py` | Clean customers → `processed/customers_cleaned.csv` |
| 3 | `src/transform/products_cleaning.py` | Clean products → `processed/products_cleaned.csv` |
| 4 | `src/transform/orders_cleaning.py` | Clean orders → `processed/orders_cleaned.csv` |
| 5 | `src/transform/revenue_enrichment.py` | Enrich revenue → `processed/order_revenue.csv` |
| 6 | `src/load/load_to_sql.py` | Load all CSVs into PostgreSQL staging tables |
| 7 | `sql/staging/create_staging_tables.sql` | (Run before step 6 if tables don't exist) |
| 8 | `sql/dimensions/*.sql` | Build dimension tables from staging |
| 9 | `sql/facts/fact_orders.sql` | Build fact table |
| 10 | `sql/views/business_views.sql` | Create analytical views |
| 11 | `sql/validation/validate_all.sql` | Validate data integrity |

---

## 9. Star Schema Design

```
                    ┌───────────────┐
                    │   dim_date    │
                    │ ─────────────│
                    │ date_key (PK) │
                    │ full_date     │
                    │ year, quarter │
                    │ month, week   │
                    └──────┬────────┘
                           │
┌──────────────┐    ┌──────▼───────────────────────────┐
│ dim_customers│    │           fact_orders             │
│ ──────────── │    │ ─────────────────────────────────│
│ customer_sk  │◄───│ order_sk (PK)                    │
│ (PK/SK)      │    │ order_id (BK)                    │
│ customer_id  │    │ customer_sk (FK → dim_customers)  │
│ unique_id    │    │ purchase_date_key (FK → dim_date)  │
│ city, state  │    │                                   │
└──────────────┘    │ MEASURES:                         │
                    │   order_revenue                   │
                    │   order_freight                   │
                    │   order_total                     │
                    │   order_item_count                │
                    │   delivery_duration_days          │
                    │   is_late_delivery                │
                    └──────────────────────────────────┘
                    
Note: Product dimension joins via stg_order_items for item-level analysis.
```

**Grain:** One row per order  
**Modelling approach:** Kimball dimensional modelling  
**Key design decisions:**
- Surrogate keys on all dimensions (SERIAL / IDENTITY)
- Business keys preserved alongside surrogate keys
- Degenerate dimensions (`order_id`, `order_status`) stored in fact table
- Date dimension pre-built for the full dataset date range

---

## 10. Power BI Dashboard Overview

The `dashboards/olist_dashboard.pbix` file contains four report pages:

### Page 1: Sales Overview
- Total Revenue (Card)
- Total Orders (Card)
- AOV (Card)
- Monthly Revenue Trend (Line chart)
- Revenue by Quarter (Bar chart)
- MoM Revenue Growth % (Line chart)

### Page 2: Product Performance
- Revenue by Category (Horizontal bar)
- Top 10 Products by Revenue (Table)
- Category contribution treemap
- Avg Item Price by Category (Bar)

### Page 3: Regional Performance
- Revenue by State (Filled map + Bar chart)
- Top 10 Cities by Revenue
- Late Delivery % by State (Heat table)

### Page 4: Delivery Performance
- On-Time vs Late Delivery (Donut chart)
- Monthly Late Delivery % Trend (Line)
- Avg Delivery Duration by State (Bar)
- Delivery Duration Distribution (Histogram)

### DAX Measures (key examples)

```dax
Total Revenue = SUM(fact_orders[order_revenue])

Total Orders = COUNTROWS(fact_orders)

AOV = DIVIDE([Total Revenue], [Total Orders])

Revenue Growth MoM % = 
VAR CurrentRevenue = [Total Revenue]
VAR PrevRevenue = CALCULATE([Total Revenue], DATEADD(dim_date[full_date], -1, MONTH))
RETURN DIVIDE(CurrentRevenue - PrevRevenue, PrevRevenue)

On-Time Delivery % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_orders), fact_orders[is_late_delivery] = FALSE()),
    CALCULATE(COUNTROWS(fact_orders), NOT ISBLANK(fact_orders[is_late_delivery]))
)

Revenue per Customer = DIVIDE([Total Revenue], DISTINCTCOUNT(fact_orders[customer_sk]))
```

---

## 11. Key Insights

1. **Black Friday Impact:** November 2017 generated ~2.4× the average monthly revenue — logistics capacity must be pre-staged for Q4.

2. **São Paulo Dominance:** SP accounts for ~42% of revenue but only ~22% of Brazil's population, suggesting strong untapped potential in other regions.

3. **Delivery Improvement:** Average delivery duration fell from ~15 days (2016) to ~10 days (mid-2018), demonstrating logistics maturation.

4. **Low Repeat Rates:** Only ~3% of customers place a second order — CRM and retention programmes represent the single highest-ROI investment available.

5. **Category Concentration:** The top 5 categories account for ~45% of GMV; bottom 20 categories combined contribute < 5%.

See `docs/insights_summary.md` for the full analysis and strategic recommendations.

---

## 12. Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run a specific test class
pytest tests/test_transformations.py::TestCustomersTransformations -v
```

Test coverage includes:
- Validation utility functions (null checks, duplicate checks, date order, FK checks)
- Customer transformation logic (state normalisation, city standardisation, deduplication)
- Order transformation logic (timestamp parsing, status normalisation, delivery flags)
- Revenue calculation logic (delivery duration, late delivery detection)

---

## 13. Project Standards

| Standard | Implementation |
|----------|---------------|
| **No hardcoded paths** | All paths via `pathlib.Path` in `config.py` |
| **No hardcoded credentials** | Environment variables only |
| **Logging** | `logging` module throughout; no `print()` statements |
| **Idempotency** | All scripts safe to re-run |
| **Type hints** | Applied to all function signatures |
| **Docstrings** | Google-style on all functions and modules |
| **Error handling** | `try/except` with specific exception types |
| **Code style** | PEP 8 compliant |
| **Reproducibility** | Full pipeline reproducible from clean state with one command sequence |

---

## Acknowledgements

Dataset: [Olist](https://www.olist.com) via [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
Methodology: [Kimball Group — The Data Warehouse Toolkit](https://www.kimballgroup.com)
