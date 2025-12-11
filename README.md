# DataSmartPLS4.0

**DataSmartPLS4.0** is an advanced synthetic survey data generator designed for **SmartPLS**, **PLS-SEM**, **CB-SEM**, **fsQCA**, **IMPA**, and broader behavioral modeling applications.  
It produces **realistic, psychometrically valid, multi-construct datasets** based on latent variable models, configurable measurement structures, response biases, structural relations, and multi-group analyses.

This tool is developed as part of the **B’Deshi Emerging Research Lab** ecosystem.

---

## 🚀 Vision of the Tool

This repository will evolve into a **fully professional, multi-module synthetic data generation suite** that supports:

### ✔ Reflective measurement model simulation  
### ✔ Advanced latent distributions  
- normal  
- skewed  
- kurtotic  
- uniform  
- lognormal  
- beta  
- mixture distributions  

### ✔ Structural model simulation  
- PLS-SEM & CB-SEM  
- mediation  
- moderation  
- higher-order constructs  
- path coefficient control  
- R²-driven latent scores  

### ✔ Response behaviour simulation  
- careless responses  
- straight-lining  
- acquiescence bias  
- midpoint bias  
- extremity bias  
- social desirability effects  
- missing data (MCAR, MAR, MNAR)  
- outlier generation  

### ✔ Demographics & multi-group modeling  
- configurable demographic distributions  
- group-specific means, variances, and structural effects  
- simulation for MGA / MICOM  

### ✔ Diagnostics dashboard  
- Cronbach’s alpha  
- Composite reliability  
- AVE  
- HTMT  
- VIF  
- item correlation matrix  
- R², Q², f²  
- visualizations (heatmaps, distributions, boxplots)  

### ✔ Export formats  
- CSV  
- Excel  
- SPSS (.sav)  
- Stata (.dta)  
- R (.rds)  
- Auto-generated codebook  
- SmartPLS-ready dataset bundle  

### ✔ Streamlit multi-page interface  
- Modular UI  
- Step-by-step configuration  
- Real-time diagnostics  
- Download center  
- Custom branding  

---

## 🧱 Repository Roadmap (V1 → V5 Combined)

The development plan integrates **all levels** of complexity within the same build:

### **Phase 1 — Core Measurement Engine**
- Latent variable generation  
- Item-level reflective indicators  
- Likert mapping  
- Loading structures  
- Multi-construct generator  

### **Phase 2 — Advanced Realism**
- bias simulation  
- missingness  
- outliers  
- noise models  

### **Phase 3 — Structural Model Engine**
- PLS paths  
- mediation / moderation  
- second-order constructs  
- group-specific models  

### **Phase 4 — Diagnostics**
- reliability  
- validity  
- structural diagnostics  
- graphs & visualizations  

### **Phase 5 — UI + Export System**
- Streamlit multi-page interface  
- Data export center  
- Codebook generator  
- Branding & aesthetics  

---

## 📁 Planned Repository Structure
DataSmartPLS4.0/
│
├─ app/ # Streamlit app (multi-page UI)
│ ├─ Home.py
│ ├─ MeasurementModel.py
│ ├─ StructuralModel.py
│ ├─ ResponseBias.py
│ ├─ Demographics.py
│ ├─ Diagnostics.py
│ └─ ExportCenter.py
│
├─ core/ # Core simulation logic (Python)
│ ├─ config.py
│ ├─ latent.py
│ ├─ measurement.py
│ ├─ bias.py
│ ├─ structural.py
│ ├─ demographics.py
│ ├─ diagnostics.py
│ └─ generator.py
│
├─ utils/ # Helpers, plotting, exporting
│ ├─ plotting.py
│ ├─ export.py
│ └─ helpers.py
│
├─ examples/ # Example notebooks & datasets
│
├─ tests/ # Automated tests (optional)
│
├─ README.md
├─ LICENSE
├─ .gitignore
└─ requirements.txt
