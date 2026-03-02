# Grid-Scale BESS Pipeline Intelligence
### CAISO & AEMO Interconnection Queue Analysis | 2024–2035

📊 **[View the Interactive Dashboard live on Tableau Public →](https://public.tableau.com/app/profile/sarthak.rokade/viz/BESSTracker/Dashboard3?publish=yes&showOnboarding=true)**

Dashboard Snapshot : 

<img width="1386" height="678" alt="Screenshot 2026-03-02 at 3 45 30 AM" src="https://github.com/user-attachments/assets/8687c4f3-e341-4288-b33b-2e449e526a2f" />



## 🌐 Overview
An automated data pipeline that ingests, normalizes, and structures battery storage project data from two heterogeneous sources—CAISO's interconnection queue and AEMO's project register—into a unified, analytics-ready dataset powering a Tableau market intelligence dashboard.

## 🛑 The Problem
CAISO and AEMO publish interconnection queue data in entirely different formats, schemas, and update cadences. Extracting macro-level market insights requires standardizing project status classifications, handling missing duration data, resolving duplicate entries, and aligning geographic hierarchies across two completely distinct grid systems.

## 💡 What This Pipeline Does
- Ingests raw queue data from CAISO and AEMO sources.
- Standardizes project status classifications and schemas across both markets.
- Models missing CAISO duration data as a configurable parameter for dynamic scenario testing.
- Outputs clean, standardized `.csv` staging files optimized for a native data union inside Tableau.

## 🔑 Key Findings
- **26.8 GW / 102 GWh** of standalone BESS capacity currently in the active pipeline.
- Peak deployment window identified between **2027–2029**, representing ~68% of the total pipeline.
- Average battery duration is trending toward the **4-hour industry standard** by 2031.
- CAISO development cycles are heavily bottlenecked, rising from **2 years to 7+ years** post-queue reform.
- **NSW1** (Australia) and **San Bernardino** (California) are emerging as the highest-concentration storage markets.

| Source | Market | Raw Data Link |
|---|---|---|
| CAISO Interconnection Queue | California, USA | [Download CAISO Cluster 15 (.xlsx)](https://www.caiso.com/documents/cluster-15-interconnection-requests.xlsx) |
| AEMO Generator Information | Australia | [Download AEMO Jan 2026 (.xlsx)](https://www.aemo.com.au/-/media/files/electricity/nem/planning_and_forecasting/generation_information/2026/nem-generation-information-jan-2026.xlsx?rev=1f6bccf827284f9fb6d6f3ae56ed3fe9&sc_lang=en) |

## ⚙️ Core Pipeline Logic & Engineering Highlights
The Python ETL script (`Global BESS Tracker.py`) standardizes highly inconsistent regional grid data. Key engineering features include:
* **Schema Sanitization:** Implemented programmatic column stripping prior to dataset concatenation to resolve aggressive schema mismatches (e.g., hidden trailing spaces in CAISO headers causing `NaT` datetime dropouts).
* **Technology Parsing:** Engineered a classification function to accurately isolate BESS capacity from complex Hybrid (Solar+BESS and Wind+BESS) project strings.
* **Developer Obfuscation Handling:** Built conditional logic to extract explicit `Site Owner` data for the transparent Australian market, while standardizing anonymous LLCs in the US market as "Undisclosed (CAISO Policy)" to maintain data integrity.
* **Cycle Time Math:** Isolated datetime calculations (Queue Date to COD) to generate a `Dev_Cycle_Years` metric, quantifying the true time-in-queue bottleneck for developers.

## 📈 Tableau Dashboard Features
The resulting staging files are unioned natively in Tableau to feed an executive-level dashboard:
* **Dynamic Scenario Modeling:** Includes a custom parameter allowing users to stress-test CAISO energy capacity (MWh) based on variable grid duration assumptions (e.g., 2-hour vs. 4-hour systems).
* **Multi-Layered Tooltips (Viz in Tooltip):** Embedded pie charts within hover states to reveal the underlying Standalone vs. Hybrid technology split for any given year.
* **Interactive Filtering:** Dashboard components are linked via Set Actions, allowing users to seamlessly filter the entire global view by Developer, Market Operator, or Project Status.

## 📝 Technical Notes & Assumptions
- CAISO does not publish duration data at the project level; it is modeled as an adjustable parameter (defaulting to 4hr).
- Project withdrawal data is currently only available and factored in for CAISO.
- Explicit developer concentration data is only publicly available for AEMO.
- The pipeline applies a primary filter to isolate Battery Storage projects by default and Project Status as In Construction and Proposed.

## 🚀 How to Run the Pipeline locally
1. Clone this repository to your local machine.
2. Ensure you have the required Python libraries installed:
   ```bash
   pip install pandas numpy openpyxl
