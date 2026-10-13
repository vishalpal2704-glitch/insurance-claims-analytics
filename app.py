import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Motor Insurance Claims Analytics", layout="wide")

FREQ_PATH = "freMTPL2freq.xlsx"
SEV_PATH = "freMTPL2sev.csv"


@st.cache_data
def load_data():
    freq = pd.read_csv(FREQ_PATH)
    sev = pd.read_csv(SEV_PATH)

    # --- Cleaning & preparation ---
    freq = freq.drop_duplicates()
    freq["Exposure"] = freq["Exposure"].clip(upper=1)    # exposure cannot exceed one year
    freq["ClaimNb"] = freq["ClaimNb"].clip(upper=4)      # cap extreme claim counts
    freq["VehAge"] = freq["VehAge"].clip(upper=20)       # cap implausible vehicle ages
    freq["DrivAge"] = freq["DrivAge"].clip(upper=90)     # cap implausible driver ages

    loss = sev.groupby("IDpol").ClaimAmount.sum().rename("Loss")
    df = freq.merge(loss, on="IDpol", how="left").fillna({"Loss": 0})

    df["DriverAgeBand"] = pd.cut(df.DrivAge, [17, 24, 34, 44, 54, 64, 100],
                                 labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
    df["VehicleAgeBand"] = pd.cut(df.VehAge, [-1, 0, 2, 5, 10, 15, 100],
                                  labels=["New (0)", "1-2", "3-5", "6-10", "11-15", "16+"])
    df["BonusMalusBand"] = pd.cut(df.BonusMalus, [0, 50, 60, 80, 100, 300],
                                  labels=["50 (best)", "51-60", "61-80", "81-100", "100+ (worst)"])
    df["DensityBand"] = pd.cut(df.Density, [-1, 100, 500, 2000, 10000, 100000],
                               labels=["<100", "100-500", "500-2k", "2k-10k", "10k+"])
    return df


def summarise(d, by):
    g = d.groupby(by, observed=True).agg(
        Policies=("IDpol", "count"), Exposure=("Exposure", "sum"),
        Claims=("ClaimNb", "sum"), Loss=("Loss", "sum")).reset_index()
    g["Claim Frequency"] = g.Claims / g.Exposure
    g["Pure Premium"] = g.Loss / g.Exposure
    return g


df = load_data()

st.title("Motor Third-Party Liability Insurance - Claims Analytics")
st.caption("Business question: which policyholder, vehicle and location segments drive claim frequency "
           "and cost, and where should the insurer focus pricing and underwriting?")

# ---------------- Filters ----------------
st.sidebar.header("Filters")


def pick(label, col):
    opts = sorted(df[col].astype(str).unique())
    return st.sidebar.multiselect(label, opts, default=opts)


areas = pick("Area (A = rural, F = urban)", "Area")
regions = pick("Region", "Region")
brands = pick("Vehicle brand", "VehBrand")
gas = pick("Fuel type", "VehGas")
dage = st.sidebar.slider("Driver age", 18, 90, (18, 90))
vage = st.sidebar.slider("Vehicle age", 0, 20, (0, 20))

f = df[df.Area.isin(areas) & df.Region.isin(regions) & df.VehBrand.isin(brands) & df.VehGas.isin(gas)
       & df.DrivAge.between(*dage) & df.VehAge.between(*vage)]
if f.empty:
    st.warning("No policies match the selected filters.")
    st.stop()

# ---------------- KPIs ----------------
exp, claims, loss = f.Exposure.sum(), f.ClaimNb.sum(), f.Loss.sum()
k = st.columns(5)
k[0].metric("Policies", f"{len(f):,}")
k[1].metric("Exposure (policy-years)", f"{exp:,.0f}")
k[2].metric("Claim frequency", f"{claims / exp:.1%}", help="Claims per policy-year")
k[3].metric("Total claim cost (EUR)", f"{loss:,.0f}")
k[4].metric("Pure premium (EUR/yr)", f"{loss / exp:,.0f}", help="Claim cost per policy-year of exposure")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Risk drivers", "Geography", "Insights & Recommendations", "Data & Method"])


def bar_pair(col, title):
    g = summarise(f, col)
    a, b = st.columns(2)
    a.plotly_chart(px.bar(g, x=col, y="Claim Frequency", title=f"Claim frequency by {title}",
                          labels={"Claim Frequency": "Claims per policy-year"}), width="stretch")
    b.plotly_chart(px.bar(g, x=col, y="Pure Premium", title=f"Pure premium by {title}",
                          labels={"Pure Premium": "EUR per policy-year"}), width="stretch")


with tab1:
    a, b = st.columns(2)
    a.plotly_chart(px.histogram(f[f.ClaimNb >= 0], x="ClaimNb", title="Distribution of claims per policy",
                                labels={"ClaimNb": "Number of claims"}).update_yaxes(type="log", title="Policies (log scale)"),
                   width="stretch")
    sev = pd.read_csv(SEV_PATH)
    sev = sev[sev.IDpol.isin(f.IDpol)]
    b.plotly_chart(px.histogram(sev[sev.ClaimAmount < sev.ClaimAmount.quantile(0.99)], x="ClaimAmount", nbins=60,
                                title="Claim amount distribution (below 99th percentile)",
                                labels={"ClaimAmount": "Claim amount (EUR)"}), width="stretch")
    st.write(f"Median claim: **EUR {sev.ClaimAmount.median():,.0f}**, mean: **EUR {sev.ClaimAmount.mean():,.0f}**, "
             f"max: **EUR {sev.ClaimAmount.max():,.0f}** - a heavy right tail: a few large claims drive the average.")

with tab2:
    bar_pair("DriverAgeBand", "driver age")
    bar_pair("VehicleAgeBand", "vehicle age")
    bar_pair("BonusMalusBand", "bonus-malus band")
    bar_pair("VehBrand", "vehicle brand")
    c = f[["ClaimNb", "Exposure", "VehPower", "VehAge", "DrivAge", "BonusMalus", "Density", "Loss"]].corr()
    st.plotly_chart(px.imshow(c, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                              title="Correlation matrix"), width="stretch")

with tab3:
    bar_pair("Area", "area")
    bar_pair("DensityBand", "population density (inhabitants/km2)")
    g = summarise(f, "Region").sort_values("Pure Premium", ascending=False)
    st.plotly_chart(px.bar(g, x="Region", y="Pure Premium", hover_data=["Exposure", "Claims"],
                           title="Pure premium by region (EUR per policy-year)"), width="stretch")
    st.caption("Regions with very low exposure (e.g. Champagne-Ardenne, Alsace, Franche-Comte) have volatile results.")

with tab4:
    st.subheader("Key findings (full portfolio, exposure-weighted)")
    st.markdown("""
1. **Bonus-malus is the strongest risk signal.** Policyholders with a score above 80 claim 2.2-4.7x as often as
   those at the best level of 50 (about 18% and 38% vs 8% claims per policy-year), and their pure premium is 5-7x higher
   (about EUR 550-720 vs EUR 99).
2. **Young drivers (18-24) are the costliest segment.** Their claim frequency (~19%) is roughly double that of
   other age groups (~9-10%) and their pure premium (~EUR 940) is about 6-8x that of other groups (EUR 119-154).
3. **Urban areas have higher claim frequency.** Frequency rises steadily from Area A (~8.2%) to Area F (~13.9%),
   and Ile-de-France has a high frequency (~13%) but a low claim cost. Rhone-Alpes and Centre produce the largest
   total losses.
4. **Brand, vehicle age and fuel differ in more nuanced ways.** Brand B12 has a high frequency (~13.7%) but low
   cost per claim; new vehicles (age 0) have a very high frequency, which is partly an artefact of short exposure.
   Vehicles aged 11-15 have the highest pure premium (~EUR 228). Fuel type shows almost no difference
   (~EUR 162 diesel vs ~EUR 172 petrol).
""")
    st.subheader("Recommendations")
    st.markdown("""
- **Price on bonus-malus and young-driver age more aggressively.** These two factors separate risk the most, so
  under-priced high-malus and 18-24 policies are the most likely to be cross-subsidised by good drivers.
- **Apply urban/density loadings and monitor Area E-F and Ile-de-France**, while using loss-control steps
  (telematics, repair networks) where frequency is high but severity is moderate.
- **Review older vehicles (11-15 years) and brands with high cost per claim (e.g. B11, B2)** for underwriting
  or deductible adjustments; do not rely on fuel type as a rating factor.
- **Use credibility rules for small regions** before changing prices, because their results are volatile.
- **Manage large-loss exposure** (reinsurance or caps in modelling), since a few very large claims distort averages.
""")

with tab5:
    st.markdown(f"""
**Dataset:** freMTPL2 (French Motor Third-Party Liability), from the `CASdatasets` R package; available on
OpenML (freMTPL2freq ID 41214, freMTPL2sev ID 41215). Frequency file: {len(df):,} policies; severity file: claim amounts per policy.

**Preparation:** duplicates removed; Exposure capped at 1 year; ClaimNb capped at 4; vehicle age capped at 20; driver age
capped at 90; claim amounts summed per policy and joined to the policy file; unmatched policies get zero loss; age,
vehicle-age, bonus-malus and density bands created.

**Metrics:** claim frequency = claims / exposure; pure premium = total claim cost / exposure.

**Data dictionary:**
| Variable | Meaning |
|---|---|
| IDpol | Policy ID |
| ClaimNb | Number of claims |
| Exposure | Policy-years in force |
| VehPower | Vehicle power (ordered categories) |
| VehAge / DrivAge | Vehicle / driver age in years |
| BonusMalus | Bonus-malus level (50 = best; above 100 = malus) |
| VehBrand | Anonymised vehicle brand |
| VehGas | Diesel or regular fuel |
| Area | Density-based area code (A rural to F urban) |
| Density | Inhabitants per km2 of the policy city |
| Region | French region |
| ClaimAmount | Claim cost (severity file) |
""")
    st.dataframe(f.head(200))
