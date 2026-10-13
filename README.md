# Motor Insurance Claims Analytics (Streamlit Dashboard)

CA4 Capstone Project - Business Analytics (IBA, 5th Semester).

## Project overview
An interactive Streamlit dashboard that analyses French motor third-party liability (MTPL) insurance policies and claims to answer:
*which policyholder, vehicle and location segments drive claim frequency and claim cost, and where should the insurer focus pricing and underwriting?*

The dashboard provides KPIs (policies, exposure, claim frequency, total claim cost, pure premium), sidebar filters (area, region, vehicle brand, fuel, driver age, vehicle age), charts by risk driver and geography, a correlation matrix, and a tab with business insights and recommendations.

## Dataset source
**freMTPL2** (French Motor Third-Party Liability), a real public-domain insurance dataset from the R package **CASdatasets** (Dutang & Charpentier).
- OpenML freMTPL2freq: https://www.openml.org/d/41214
- OpenML freMTPL2sev: https://www.openml.org/d/41215
- CASdatasets: http://cas.uqam.ca

Files in `data/`:
- `freMTPL2freq.csv` - 678,013 policies (exposure, claim count, driver/vehicle/location attributes)
- `freMTPL2sev.csv` - 26,639 claim amounts linked to policies by `IDpol`

The data is anonymised and public; no confidential, private or restricted data is included.

## Technology used
Python, Pandas, NumPy, Plotly, Streamlit, GitHub

## Data preparation
Duplicates removed; exposure capped at 1 year; claim count capped at 4; extreme vehicle and driver ages capped; claim amounts summed per policy and joined to the policy table; age, vehicle-age, bonus-malus and density bands created.
Claim frequency = claims / exposure; pure premium = claim cost / exposure.

## How to run
```bash
git clone https://github.com/vishalpal2704-glitch/insurance-claims-analytics.git
cd insurance-claims-analytics
pip install -r requirements.txt
streamlit run app.py
```

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit application |
| `requirements.txt` | Python dependencies |
| `data/` | Original public dataset files |

## Links
- GitHub repository: https://github.com/vishalpal2704-glitch/insurance-claims-analytics
- Streamlit app: _add deployed link here after Step 9_
