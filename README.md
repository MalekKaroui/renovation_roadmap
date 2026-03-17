```markdown
# The Renovation Roadmap

**Predicting early signs of gentrification in Saint John, New Brunswick using building permit data**

This project analyzes 10 years of building permits in Saint John, NB to identify areas where investment may be arriving before property values fully adjust. The main idea is to treat building permits as a **leading indicator** of neighborhood change instead of just an administrative record.

## Project Goal

Cities usually notice gentrification after property values spike and residents start feeling the effects. I wanted to see if I could detect that change earlier by looking at building permits, spatial patterns, and property assessments.

The project asks:

- Where are high-value permits clustering?
- Which areas are changing fastest over time?
- Are there areas receiving strong investment even though their assessed property values are still low?

## Key Result

The strongest result from the project is the **Investment-Assessment Ratio (IAR)**:

```text
IAR = mean permit value / mean assessed property value
```

Using that metric, I identified:

- **15 pre-gentrification grid cells**
- **1 statistically significant hotspot** using Getis-Ord analysis
- **1 strongly emerging cell** with about **71% annual growth**

The strongest case was:

- **GRID_03_16**
- Mean permit value: **$2,215,000**
- Mean assessed value: **$104,893**
- **IAR = 21.1**

This suggests that investment is moving into that area much faster than official property values are adjusting.

## Methods Used

This project combines data cleaning, spatial analysis, clustering, statistical hotspot detection, and temporal analysis.

Main methods:

- **K-Means clustering**
- **DBSCAN**
- **Getis-Ord G\* hotspot analysis**
- **Temporal CAGR analysis**
- **Investment-Assessment Ratio (IAR)**

## Data Summary

### Building Permits
- Source: City of Saint John Open Data Catalogue
- Raw records: **30,287**
- Final cleaned records: **1,098**
- Total investment represented: **$255,986,293**

### Property Assessments
- Source: City of Saint John Open Data Catalogue
- Records: **76,394**
- Valid after cleaning: **76,271**

## Main Findings

- Permit activity is not evenly spread across Saint John
- One grid cell, **GRID_10_10**, stood out with:
  - **75 permits**
  - Mean permit value of about **$585,420**
  - CAGR of about **71%**
- K-Means found useful geographic/value patterns, but not enough by itself to detect early-stage change
- DBSCAN showed that permit activity is spatially connected rather than split into many isolated clusters
- Getis-Ord found **1 significant hotspot**
- IAR was the clearest way to identify early-stage gentrification signals

## Repository Structure

```text
renovation_roadmap/
├── src/                    # Python source files
├── data/                   # Processed datasets
├── outputs/figures/        # Generated visualizations
├── main.py                 # Main pipeline runner
├── dashboard.py / src/     # Streamlit dashboard
├── requirements.txt
└── final_report.tex / pdf
```

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/MalekKaroui/renovation-roadmap.git
cd renovation-roadmap
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the full pipeline
```bash
python main.py
```

### 5. Run the dashboard
```bash
streamlit run src/dashboard.py
```

## Dashboard

I also built a Streamlit dashboard to present the results in an interactive way. It includes:

- Executive summary
- Spatial analysis
- Temporal trends
- Hotspot detection
- IAR analysis
- Raw data explorer

## Why This Project Matters

This project is important because it shows how data mining can support more proactive urban planning. Instead of waiting for neighborhoods to change and then reacting, cities may be able to use permit data as an early warning system.

## Academic Context

- **Course:** CS 4403 Data Mining
- **Student:** Malek Karoui
- **Student Number:** 3751935
- **Institution:** University of New Brunswick

## GitHub

Repository link:

**https://github.com/MalekKaroui/renovation-roadmap**

## License

MIT License
```
