# 🚀 Smart Data Analyzer — Data Intelligence & Validation Platform

A full-stack Python analytics system built to diagnose data quality, infer schema structure, and generate reliable insights before analysis or modeling.

Most student projects visualize data.  
This system is built to understand whether the data should be trusted in the first place.

It ingests datasets, applies configurable cleaning pipelines, runs automated validation and schema inference, computes a data-quality score, generates insights, and produces exportable reports — all backed by a persistent storage layer.

---

## 🎯 Problem & Motivation

In real analytics and ML workflows, the biggest failures don’t come from models — they come from bad data.

Common issues:
- identifier columns treated as features  
- hidden duplicates  
- mislabeled types  
- silent outliers  
- constant or misleading columns  

These problems lead to incorrect conclusions and broken pipelines.

This project was built to act as a data gatekeeper — a system that evaluates dataset structure, reliability, and readiness before analysis or modeling begins.

---

## 🖥️ Demo

Add screenshots in `assets/screenshots/` if you want a visual portfolio section. The app currently ships without committed image assets.

---

## ✨ Core Capabilities

### 🔹 Ingestion & Cleaning Engine
- CSV ingestion with defensive parsing  
- Modular preprocessing pipeline  
- Duplicate removal, numeric imputation, categorical normalization  
- Numeric auto-conversion & whitespace standardization  
- Before/after dataset inspection  
- Cleaning summary with measurable transformations  

---

### 🔹 Dataset Validation & Schema Intelligence
- Identifier-like column detection  
- Constant / near-constant column detection  
- Datetime feature inference  
- High-cardinality categorical detection  
- Numeric-as-categorical detection  
- Distribution risk diagnostics  

Produces structured diagnostics and schema summaries describing the role, reliability, and risk of each column.

---

### 🔹 Data Quality Scoring System
- Quantitative 0–100 reliability score  
- Penalty-based evaluation using missingness, duplicates, constants, anomalies, and instability  
- Interpretable breakdown surfaced in UI and reports  

---

### 🔹 Analytics & Visualization Layer
- Missing-value profiling  
- Numeric statistics + medians  
- Categorical frequency analysis  
- Correlation matrices  
- IQR-based outlier detection  
- Interactive histograms, box plots, scatter plots, and categorical bar charts  

---

### 🔹 Automated Insight Engine
- Flags high-risk columns  
- Detects structural anomalies  
- Surfaces strong correlations  
- Highlights dominant categories  
- Emits validation warnings  

---

### 🔹 Persistence & Reproducibility
- SQLite backend storing datasets, cleaned snapshots, and reports  
- Historical analysis browser  
- Reproducible analytics workflows  

---

### 🔹 Reporting & Export
- Downloadable cleaned datasets  
- Auto-generated analysis reports  
- Embedded diagnostics & quality scoring  
- Report previews and history  

---

## 🏗️ System Architecture
CSV Ingestion
↓
Cleaning Engine
↓
Validation & Schema Intelligence
↓
Analytics & Computation
↓
Automated Insights
↓
Report Generation
↓
SQLite Persistence Layer

The system is modularized into independent engines for preprocessing, validation, analytics, insights, reporting, and storage.

---

## 🛠️ Tech Stack

Languages & Core  
- Python  

Frameworks & Libraries  
- Streamlit  
- Pandas  
- NumPy  
- Matplotlib  

Backend & Storage  
- SQLite (sqlite3)  

Engineering Concepts  
- ETL-style pipeline design  
- Schema inference  
- Data validation systems  
- Diagnostic scoring frameworks  
- Persistent storage layers  
- Modular architecture  
- Separation of concerns  
- Defensive programming  
- Reproducible workflows  
- Performance caching  

---

## 📁 Example Project Structure

```text
app.py
storage.py
validation.py
requirements.txt
README.md
.streamlit/config.toml

app/
  theme.css

services/
  analytics.py
  cleaning.py
  reporting.py

tests/
  conftest.py
  test_cleaning.py
  test_quality_score.py
  test_validation.py

ui/
  sidebar.py
  sections.py
```

---

## ▶️ Running the Project

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open in browser:
`http://localhost:8501`

## 📊 Example Use Cases

- Survey and research dataset validation
- Pre-modeling data audits
- Business and retail dataset diagnostics
- Feature health checks
- Academic experiment analysis
- Automated exploratory data analysis

---

## 🧠 Engineering Highlights

- Designed a full analytics pipeline: ingest → clean → validate → analyze → report → persist
- Implemented a schema inference and dataset diagnostics engine
- Built a quantitative data-quality scoring framework
- Engineered a persistent backend layer for reproducible workflows
- Developed an automated insight and reporting system

---

## 🚧 Future Extensions

- Pipeline versioning and replay
- Background job processing
- Feature recommendation engine
- Cloud database migration
- Scheduled dataset monitoring
- User profiles and access control

---

👤 Author

Built by Angad Singh
Focused on software engineering, analytics systems, and data platform design.

---

# 📸 COPY-PASTE SCREENSHOT CHECKLIST

```markdown
## 📸 Screenshot Checklist

Create folder:
`assets/screenshots/`

Take high-resolution screenshots of:

1) Upload & Cleaning  
   - file upload  
   - cleaning toggles  
   - cleaning summary  
   - raw vs cleaned preview  
   → upload_cleaning.png

2) Dataset Diagnostics  
   - schema validation  
   - warnings  
   - column role detection  
   → diagnostics.png

3) Data Quality Score  
   - score metric  
   - penalty breakdown  
   → quality_score.png

4) Analytics & Visuals  
   - charts  
   - statistics tables  
   - correlation matrix  
   → analytics_visuals.png

5) Automated Insights  
   - generated insights  
   - warnings  
   → insights.png

6) Persistence & History  
   - saved datasets  
   - report history  
   → history.png

Insert near top of README:

![Upload & Cleaning](assets/screenshots/upload_cleaning.png)
![Dataset Diagnostics](assets/screenshots/diagnostics.png)
![Data Quality Score](assets/screenshots/quality_score.png)
![Analytics](assets/screenshots/analytics_visuals.png)
![Insights](assets/screenshots/insights.png)
![History](assets/screenshots/history.png)
