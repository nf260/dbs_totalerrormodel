import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(page_title="Minimum DBS diameter modelling", layout="centered")

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
    index=0
)
z = confidence_options[confidence_choice]

# Sliders
cv_value = st.sidebar.slider(
    "Analytical CV (%)", min_value=0.0, max_value=30.0, value=8.7, step=0.1
)
tea_value = st.sidebar.slider(
    "Total Allowable Error (TEa, %)", min_value=5.0, max_value=50.0, value=25.0, step=0.5
)
bias_anal_max = st.sidebar.slider(
    "Analytical Bias (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1
)

factor = st.sidebar.slider(
    "% change per mm", min_value=0.0, max_value=5.0, value=2.74, step=0.01
)

reference_size = st.sidebar.slider(
    "Reference DBS diameter", min_value=10.0, max_value=12.0, value=10.7, step=0.1
)

# --- Data calculation ---
cv_values = np.linspace(0, 30, 200)
df = pd.DataFrame({"Analytical CV (%)": cv_values})
df["z×CV (%)"] = z * df["Analytical CV (%)"]
df["Max allowable bias (%)"] = tea_value - df["z×CV (%)"]
df["Max bias (DBS)"] = df["Max allowable bias (%)"] - bias_anal_max
df["Max mm difference"] = df["Max bias (DBS)"] / factor
df["Min size"] = reference_size - df["Max mm difference"]

# Compute point estimate for chosen CV
chosen = df.iloc[(df["Analytical CV (%)"] - cv_value).abs().argsort()[:1]].iloc[0]
min_dbs_size = chosen["Min size"]

# --- Display metric ---
st.title("Calculated Minimum DBS Size")
st.markdown("This model complements paper {placeholder}. Adjust parameters in sidebar")

if min_dbs_size > reference_size:
    st.metric(
        label="Min acceptable DBS diameter (mm)",
        value="Not feasible"
    )
else:
    st.metric(
        label="Min acceptable DBS diameter (mm)",
        value=f"{min_dbs_size:.2f}"
    )

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

x = df["Analytical CV (%)"]
y = df["Min size"]
y_axis_max = reference_size

# Fill below (red) and above (green)
ax.fill_between(x, 0, y, color="red", alpha=0.4)
ax.fill_between(x, y, y_axis_max, color="green", alpha=0.3)

# Plot main curve
ax.plot(x, y, color="black", linewidth=2, label="Min acceptable DBS diameter")

# Draw L-shaped dotted guide at chosen CV
y_chosen = np.interp(cv_value, x, y)
ax.vlines(x=cv_value, ymin=0, ymax=y_chosen, color="black", linestyle="--", linewidth=1)
ax.hlines(y=y_chosen, xmin=0, xmax=cv_value, color="black", linestyle="--", linewidth=1)
ax.scatter(cv_value, y_chosen, color="black", s=50, zorder=5)

# Labels and title
ax.set_xlabel("Analytical CV (%)", fontsize=13)
ax.set_ylabel("Minimum acceptable DBS diameter (mm)", fontsize=13)

ax.set_ylim(0, y_axis_max)
ax.set_xlim(0, 30)
ax.grid(True)

# Legend and corner text
ax.text(0.02, 0.95, "TEA target met", transform=ax.transAxes,
        fontsize=11, fontweight="bold", ha="left", va="top")
ax.text(0.98, 0.05, "TEA target not met", transform=ax.transAxes,
        fontsize=11, fontweight="bold", ha="right", va="bottom")

st.pyplot(fig)

