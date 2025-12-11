# DataSmartPLS4.0
High-quality synthetic survey data generator for SmartPLS-4, PLS-SEM, CB-SEM, fsQCA, IMPA, and advanced behavioral modeling.  
Designed for researchers, students, and analysts who require **realistic, psychometrically valid synthetic datasets** for methodological testing, simulation studies, training, or tool development.

---

## ✨ Overview

**DataSmartPLS4.0** is a next-generation synthetic data engine capable of generating:
- Realistic reflective measurement models  
- High-quality Likert-scale item responses  
- Latent variable structures with controllable distributions  
- True factor loadings, noise components, and item properties  
- Demographic variables  
- Structural model relationships (future release)  
- Response behaviors and biases (future release)  
- Multi-group structures for MGA / MICOM (future release)  

The tool can be used for:
- SmartPLS pipeline testing  
- Teaching PLS-SEM/CB-SEM  
- fsQCA calibration training  
- Monte-Carlo-style methodology studies  
- Survey instrument prototyping  
- Generating training datasets for algorithm development  

---

## 🚀 Features (v0.1)

### ✔ Reflective Construct Generator  
- Latent variable simulation  
- Item generation via factor-loading model  
- Controlled error variance  
- Likert-scale discretization  
- Configurable number of items  
- Adjustable loading patterns  

### ✔ Base Distributions  
- Normal  
- Skewed  
- Uniform  
- Lognormal  
- Beta (bounded latent traits)  

### ✔ Synthetic Demographics  
- Gender  
- Age group  
- Income  
- Study level  
(More demographic controls coming soon.)

### ✔ Deterministic + Random Control  
- Random seed for reproducibility  
- Fully configurable parameter set  

---

## 🧱 Roadmap

### 🔹 v0.1 (Current)
- Core latent → indicator engine  
- Single/multiple reflective constructs  
- Likert-scale mapping  
- Basic demographics  
- Minimal Streamlit UI  

### 🔹 v0.2 (Next)
- Advanced distributions  
- Reverse coding  
- Cross-loadings  
- Response-style biases  
- Careless answering / straight-lining  
- Extreme and midpoint bias  
- Missing data simulation  

### 🔹 v0.3
- Structural Model Engine (PLS & CB-SEM)  
- Mediation, moderation, first-order and second-order constructs  
- Latent correlations  
- R² target control  
- Multi-group simulation  

### 🔹 v0.4
- Full diagnostics dashboard  
- Reliability and validity indices  
- HTMT, AVE, CR, VIF, KMO  
- Correlation heatmaps  
- Distribution plots  

### 🔹 v0.5
- Export options  
- CSV, Excel, SPSS, Stata, RDS  
- Auto-generated codebook  
- Auto-generated SmartPLS-ready dataset package  

### 🔹 v1.0
- Full professional tool  
- Multi-page Streamlit interface  
- Branding for **B’Deshi Emerging Research Lab**  
- Publishable as a methodology tool  

---

## 📁 Repository Structure (planned)

