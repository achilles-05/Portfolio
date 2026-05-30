# WorldQuant Alpha Competition (International Quant Championship - IQC)

## 🏆 Performance & Achievements
- **Global Rank:** 3,485
- **National Rank:** 275
- **Stage 1 Result:** Passed (Top 2% out of 150,000 participants)
- **Level:** Gold Level

---

## 📈 Overview
This repository contains a curated collection of my 40 best-performing alphas generated during the WorldQuant International Quant Championship (IQC). It highlights my quantitative research methodology, the advanced mathematical techniques used to bypass the correlation wall, and the high-performance stealth bot automation developed to generate and simulate thousands of alphas in bulk.

## 🛠️ Skills & Technologies Used
- **Quantitative Research & Alpha Generation:** Developing mathematically sound predictive trading signals based on market inefficiencies.
- **Factor Orthogonalization & Signal Isolation:** Isolating pure price-volume logic and dynamic bucketing to ensure zero correlation with saturated fundamental and mean-reversion factors.
- **Advanced Statistical Modeling:** Leveraging time-series regression (`ts_regression`), z-scores (`ts_zscore`), custom dynamic grouping (`bucket`, `densify`), and cross-sectional scaling.
- **Algorithmic Automation & Bot Development:** Engineered a Python-based stealth bot (`pyautogui`, `tkinter`) to bypass manual UI limitations and rapidly test thousands of combinations asynchronously.
- **Data Engineering & Regex Parsing:** Parsing extensive log files and scraping unstructured WorldQuant BRAIN terminal UI text to log AI analysis datasets in JSONL.
- **Python Data Science Stack:** Utilizing core data science techniques and algorithms for financial signal formulation.

---

## 🔬 Core Methodologies & Strategies

### 1. The Kakushadze Protocol (Academic Outperformance)
Leveraged peer-reviewed, structurally proven anomalies (inspired by the famous *101 Formulaic Alphas*) mathematically engineered for low pairwise correlation, guaranteeing high Sharpe and low turnover while circumventing standard mean-reversion saturation.

### 2. Dynamic Group Neutralization
Instead of using static, widely-used classifications like sector or industry (which caused correlation filter rejections), I deployed `bucket()` and `densify()` operators. By grouping the entire market into dynamic, continuous volatility and liquidity buckets, I successfully neutralized alphas against completely custom risk structures.

### 3. Pure Price-Volume Orthogonality
Removed all fundamental data metrics (value/reversal portfolio bias) and shifted entirely to price-volume architecture. The strategies isolated volatility dislocations, long-term volume accumulation profiles, and execution liquidity traps—yielding completely orthogonal factor exposure.

### 4. Advanced Regression & Cross-Sectional Scaling
Moved beyond simple moving averages by deploying `ts_regression` to calculate literal linear trendline slopes on `rel_ret_all` (relative return to market). The formulas clamped outliers using `winsorize` and normalized signals utilizing `ts_scale` to create a new dimension of mathematical modeling.

---

## 🚀 Results & Outcomes
- **Overcoming the Correlation Wall:** Systematically solved the 0.5 correlation threshold rejection trap by analyzing thousands of `final_winners.txt` passes and `ai_analysis_log.jsonl` fails to isolate the exact operators causing correlation flags.
- **Superior Sharpe and Fitness Metrics:** Achieved Sharpes exceeding 1.25+ and maxing out at over 4.0+ in certain configurations, well above the threshold requirements.
- **Stage 1 Breakthrough:** Propelled from being stuck at the correlation wall directly into the Top 2% (Qualifying for Stage 2).

## 📁 Repository Structure
- `winning_alphas.py`: Contains a curated list of the top 40 performing alphas extracted from simulation logs, complete with Sharpe and Fitness ratios.

---
*Disclaimer: These algorithms are shared for portfolio demonstration and educational purposes highlighting my quantitative research approach during the IQC.*
