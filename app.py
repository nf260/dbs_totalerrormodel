import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(page_title="Minimum and Maximum DBS diameter modelling", layout="centered")

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

# --- Data calculation ---
cv_values = np.linspace(0, 30, 200)
df = pd.DataFrame({"Analytical CV (%)": cv_values})
df["z×CV (%)"] = z * df["Analytical CV (%)"]
df["Max allowable bias (%)"] = tea_value - df["z×CV (%)"]
df["Max bias (DBS)"] = df["Max allowable bias (%)"] - bias_anal_max
df["Max mm difference"] = df["Max bias (DBS)"] / factor

# Calculate both min and max DBS sizes
df["Min size"] = reference_size - df["Max mm difference"]
df["Max size"] = reference_size + df["Max mm difference"]

# Compute point estimate for chosen CV
chosen = df.iloc[(df["Analytical CV (%)"] - cv_value).abs().argsort()[:1]].iloc[0]
min_dbs_size = chosen["Min size"]
max_dbs_size = chosen["Max size"]

# --- Display metric ---
st.title("Calculated DBS Size Range")
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

x = df["Analytical CV (%)"]
y_min = df["Min size"]
y_max = df["Max size"]

# --- Shading ---
# Green area between min and max (acceptable)
ax.fill_between(x, y_min, y_max, color="green", alpha=0.3)

# Red areas outside the acceptable region
ax.fill_between(x, 0, y_min, color="red", alpha=0.3)
ax.fill_between(x, y_max, y_max.max() + 1, color="red", alpha=0.3)

# --- Lines ---
ax.plot(x, y_min, color="black", linewidth=2, label="Min acceptable DBS diameter")
ax.plot(x, y_max, color="black", linewidth=2, linestyle="--", label="Max acceptable DBS diameter")

# Draw horizontal L-shaped guide at chosen CV only if feasible
if 0 <= min_dbs_size <= reference_size and max_dbs_size >= reference_size:
    y_chosen_min = np.interp(cv_value, x, y_min)
    y_chosen_max = np.interp(cv_value, x, y_max)

    # Horizontal lines
    ax.hlines(
        y=y_chosen_min,
        xmin=0,
        xmax=cv_value,
        color="black",
        linestyle="--",
        linewidth=1
    )
    ax.hlines(
        y=y_chosen_max,
        xmin=0,
        xmax=cv_value,
        color="black",
        linestyle="--",
        linewidth=1
    )

    # Markers
    ax.scatter(cv_value, y_chosen_min, color="black", s=50, zorder=5)
    ax.scatter(cv_value, y_chosen_max, color="black", s=50, zorder=5)


# --- Analytical Bias vertical dotted line (always shown) ---
ax.vlines(
    x=cv_value,
    ymin=0,
    ymax=y_max.max() + 1,
    color="black",
    linestyle=":",
    linewidth=1.5,
    label="Analytical CV (%)"
)

# Labels and title
ax.set_xlabel("Analytical CV (%)", fontsize=13)
ax.set_ylabel("DBS diameter (mm)", fontsize=13)
ax.set_ylim(0, y_max.max() + 1)
ax.set_xlim(0, 30)
ax.grid(True)

# Legend
green_patch = plt.Rectangle((0, 0), 1, 1, fc="green", alpha=0.3, label="Acceptable region")
red_patch = plt.Rectangle((0, 0), 1, 1, fc="red", alpha=0.3, label="Unacceptable region")

ax.legend(
    handles=[
        plt.Line2D([0], [0], color="black", lw=2, label="Min acceptable DBS diameter"),
        plt.Line2D([0], [0], color="black", lw=2, linestyle="--", label="Max acceptable DBS diameter"),
        green_patch,
        red_patch
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=2,
    frameon=True
)

st.pyplot(fig)

st.subheader("Model assumptions")

st.markdown("""
This model assumes:
1. A linear relationship between DBS diameter and results
2. No other major sources of pre-analytical variation (for example, multispotted or layered DBS, inadequate drying or haematocrit related effects)
""")
