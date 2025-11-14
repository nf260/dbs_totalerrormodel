import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(page_title="DBS diameter interval modelling", layout="centered")

# --- Sidebar inputs ---
st.sidebar.header("Adjust Parameters")

# Confidence factor options
confidence_options = {
    "95% (one-tailed)": 1.65,
    "99% (one-tailed)": 2.33,
    "95% (two-tailed)": 1.96,
    "99% (two-tailed)": 2.58
}

confidence_choice = st.sidebar.selectbox(
    "Confidence Level",
    options=list(confidence_options.keys()),
    index=0,
    key="confidence"
)
z = confidence_options[confidence_choice]

# Sliders
tea_value = st.sidebar.slider(
    "Total Allowable Error (TEa, %)", min_value=5.0, max_value=50.0, value=25.0, step=0.5, key="tea"
)
bias_anal_max = st.sidebar.slider(
    "Analytical Bias (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, key="bias"
)
cv_value = st.sidebar.slider(
    "Analytical CV (%)", min_value=0.0, max_value=30.0, value=8.7, step=0.1, key="cv"
)
factor = st.sidebar.slider(
    "% change per mm", min_value=0.0, max_value=5.0, value=2.74, step=0.01, key="factor"
)
reference_size = st.sidebar.slider(
    "Reference DBS diameter", min_value=10.0, max_value=12.0, value=10.7, step=0.1, key="ref"
)

# --- Data calculation (SWEEP OVER TEA) ---
tea_range = np.linspace(5, 50, 200)  # This is now the x-axis
df = pd.DataFrame({"TEa (%)": tea_range})

# Use selected CV for all calculations
df["z×CV (%)"] = z * cv_value
df["Max allowable bias (%)"] = df["TEa (%)"] - df["z×CV (%)"]
df["Max bias (DBS)"] = df["Max allowable bias (%)"] - bias_anal_max
df["Max mm difference"] = df["Max bias (DBS)"] / factor

df["Min size"] = reference_size - df["Max mm difference"]
df["Max size"] = reference_size + df["Max mm difference"]

# Compute point estimate for chosen TEA
chosen = df.iloc[(df["TEa (%)"] - tea_value).abs().argsort()[:1]].iloc[0]
min_dbs_size = chosen["Min size"]
max_dbs_size = chosen["Max size"]

# --- Display metric ---
st.title("Acceptable DBS Size Interval")
st.markdown("This model complements paper {placeholder}. Adjust parameters in sidebar")

if min_dbs_size > reference_size:
    min_display = "Not feasible"
elif min_dbs_size < 0:
    min_display = "0"
else:
    min_display = f"{min_dbs_size:.2f}"

if max_dbs_size < reference_size:
    max_display = "Not feasible"
else:
    max_display = f"{max_dbs_size:.2f}"

col1, col2 = st.columns(2)
col1.metric(label="Min acceptable DBS diameter (mm)", value=min_display)
col2.metric(label="Max acceptable DBS diameter (mm)", value=max_display)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

x = df["TEa (%)"]
y_min = df["Min size"]
y_max = df["Max size"]

# --- Shading ---
ax.fill_between(x, y_min, y_max, color="#b6e3b6")
ax.fill_between(x, 0, y_min, color="#f4b6b6")
ax.fill_between(x, y_max, y_max.max() + 1, color="#f4b6b6")

# --- Lines ---
ax.plot(x, y_min, color="black", linewidth=2, label="Min acceptable DBS diameter")
ax.plot(x, y_max, color="black", linewidth=2, label="Max acceptable DBS diameter")

# Guide lines for chosen TEA
if 0 <= min_dbs_size <= reference_size and max_dbs_size >= reference_size:
    y_chosen_min = np.interp(tea_value, x, y_min)
    y_chosen_max = np.interp(tea_value, x, y_max)

    ax.hlines(y=y_chosen_min, xmin=x.min(), xmax=tea_value,
              color="black", linestyle="--", linewidth=1)
    ax.hlines(y=y_chosen_max, xmin=x.min(), xmax=tea_value,
              color="black", linestyle="--", linewidth=1)

    ax.scatter(tea_value, y_chosen_min, color="black", s=50, zorder=5)
    ax.scatter(tea_value, y_chosen_max, color="black", s=50, zorder=5)

# Vertical guide for selected TEA
ax.vlines(x=tea_value, ymin=0, ymax=y_max.max() + 1,
          color="black", linestyle=":", linewidth=1.5,
          label="Selected TEa (%)")

# Labels and title
ax.set_xlabel("Total Allowable Error (TEa, %)", fontsize=13)
ax.set_ylabel("DBS diameter (mm)", fontsize=13)
ax.set_ylim(0, 20)
ax.set_xlim(tea_range.min(), tea_range.max())
ax.grid(True)

# Legend
green_patch = plt.Rectangle((0, 0), 1, 1, fc="#b6e3b6",
                            label="Allowable Total Error limit met")
red_patch = plt.Rectangle((0, 0), 1, 1, fc="#f4b6b6",
                          label="Allowable Total Error limit not met")

ax.legend(handles=[green_patch, red_patch],
          loc="upper center",
          bbox_to_anchor=(0.5, -0.15),
          ncol=2,
          frameon=True)

st.pyplot(fig)

st.subheader("Model assumptions")

st.markdown("""
This model assumes:
1. A linear relationship between DBS diameter and results  
2. No other major sources of pre-analytical variation (multispotted or layered DBS, inadequate drying, haematocrit effects)
""")
