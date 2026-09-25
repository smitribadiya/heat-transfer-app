import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="1D Composite Wall Heat Transfer",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 1D Conduction Heat Transfer Through a Composite Wall")
st.write(
    "Steady-state one-dimensional heat conduction through multiple "
    "layers of a composite wall."
)
st.divider()

# --------------------------------------------------
# MATERIAL LIBRARY (typical values near room temperature, W/m·K)
# --------------------------------------------------

MATERIALS = {
    "Custom": None,
    "Common brick": 0.72,
    "Fire clay brick": 1.0,
    "Concrete": 1.4,
    "Gypsum plaster": 0.22,
    "Plywood": 0.12,
    "Glass (window)": 0.96,
    "Fiberglass insulation": 0.040,
    "Mineral wool": 0.038,
    "Polystyrene (EPS)": 0.035,
    "Polyurethane foam": 0.026,
    "Carbon steel": 45.0,
    "Stainless steel": 16.0,
    "Aluminum": 205.0,
    "Copper": 385.0,
}

MATERIAL_NAMES = list(MATERIALS.keys())

# --------------------------------------------------
# SIDEBAR - INPUTS
# --------------------------------------------------

st.sidebar.header("🌡️ Boundary Conditions")

T_hot = st.sidebar.number_input("Hot-side temperature (°C)", value=200.0)
T_cold = st.sidebar.number_input("Cold-side temperature (°C)", value=30.0)
area = st.sidebar.number_input(
    "Wall area (m²)", min_value=0.001, value=1.0, format="%.3f"
)

if T_hot <= T_cold:
    st.sidebar.warning(
        "Hot-side temperature is not above the cold side. "
        "Heat will flow in the reverse direction (negative Q)."
    )

st.sidebar.header("🧱 Wall Layers")

num_layers = st.sidebar.number_input(
    "Number of layers", min_value=1, max_value=6, value=3, step=1
)

default_materials = ["Common brick", "Fiberglass insulation", "Gypsum plaster"]
default_thickness = [0.10, 0.05, 0.015]

layers = []

for i in range(int(num_layers)):
    st.sidebar.subheader(f"Layer {i + 1}")

    default_mat = default_materials[i] if i < len(default_materials) else "Custom"
    choice = st.sidebar.selectbox(
        f"Material {i + 1}",
        MATERIAL_NAMES,
        index=MATERIAL_NAMES.index(default_mat),
        key=f"mat_{i}",
    )

    if choice == "Custom":
        name = st.sidebar.text_input(
            f"Material name {i + 1}", value=f"Material {i + 1}", key=f"name_{i}"
        )
        k = st.sidebar.number_input(
            f"Thermal conductivity k{i + 1} (W/m·K)",
            min_value=0.0001,
            value=1.0,
            format="%.4f",
            key=f"k_{i}",
        )
    else:
        name = choice
        k = MATERIALS[choice]
        st.sidebar.caption(f"k = {k} W/m·K")

    thickness = st.sidebar.number_input(
        f"Thickness {i + 1} (m)",
        min_value=0.0001,
        value=default_thickness[i] if i < len(default_thickness) else 0.05,
        format="%.4f",
        key=f"thickness_{i}",
    )

    layers.append({"material": name, "thickness": thickness, "k": k})

# --------------------------------------------------
# CALCULATIONS
# --------------------------------------------------

# Thermal resistance of each layer: R = L / (kA)
resistances = [layer["thickness"] / (layer["k"] * area) for layer in layers]
R_total = sum(resistances)

delta_T = T_hot - T_cold
Q = delta_T / R_total          # Heat-transfer rate (W)
q_flux = Q / area              # Heat flux (W/m²)
U = 1.0 / (R_total * area)     # Overall heat-transfer coefficient (W/m²·K)

# Interface temperatures
interface_temperatures = [T_hot]
for R in resistances:
    interface_temperatures.append(interface_temperatures[-1] - Q * R)

# Interface positions
interface_x = [0.0]
for layer in layers:
    interface_x.append(interface_x[-1] + layer["thickness"])

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

st.header("📊 Results")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Thermal Resistance", f"{R_total:.4f} K/W")
c2.metric("Heat Transfer Rate", f"{Q:.2f} W")
c3.metric("Heat Flux", f"{q_flux:.2f} W/m²")
c4.metric("U-value", f"{U:.3f} W/m²·K")

st.divider()

# --------------------------------------------------
# RESISTANCE TABLE
# --------------------------------------------------

st.subheader("🧱 Thermal Resistance of Each Layer")

df = pd.DataFrame(
    {
        "Layer": [i + 1 for i in range(len(layers))],
        "Material": [l["material"] for l in layers],
        "Thickness (m)": [l["thickness"] for l in layers],
        "k (W/m·K)": [l["k"] for l in layers],
        "Resistance (K/W)": resistances,
        "Share of total R (%)": [100 * R / R_total for R in resistances],
        "Temperature drop (°C)": [Q * R for R in resistances],
    }
)

st.dataframe(
    df.style.format(
        {
            "Thickness (m)": "{:.4f}",
            "k (W/m·K)": "{:.4g}",
            "Resistance (K/W)": "{:.5f}",
            "Share of total R (%)": "{:.1f}",
            "Temperature drop (°C)": "{:.2f}",
        }
    ),
    hide_index=True,
    width="stretch",
)

# --------------------------------------------------
# INTERFACE TEMPERATURES
# --------------------------------------------------

st.subheader("🌡️ Interface Temperatures")

rows = []
for i, (x, T) in enumerate(zip(interface_x, interface_temperatures)):
    if i == 0:
        location = "Hot wall surface"
    elif i == len(interface_temperatures) - 1:
        location = "Cold wall surface"
    else:
        location = f"Interface {i} ({layers[i - 1]['material']} | {layers[i]['material']})"
    rows.append({"Location": location, "x (m)": x, "Temperature (°C)": T})

st.dataframe(
    pd.DataFrame(rows).style.format({"x (m)": "{:.4f}", "Temperature (°C)": "{:.2f}"}),
    hide_index=True,
    width="stretch",
)

# --------------------------------------------------
# TEMPERATURE DISTRIBUTION
# --------------------------------------------------

st.subheader("📈 Temperature Distribution Through the Wall")

fig, ax = plt.subplots(figsize=(10, 5))
colors = plt.cm.Pastel1(np.linspace(0, 1, max(len(layers), 3)))

T_min = min(interface_temperatures)
T_max = max(interface_temperatures)
pad = 0.08 * (T_max - T_min if T_max != T_min else 1.0)

for i, layer in enumerate(layers):
    # Shade each layer and label it
    ax.axvspan(interface_x[i], interface_x[i + 1], color=colors[i], alpha=0.6)
    ax.text(
        (interface_x[i] + interface_x[i + 1]) / 2,
        T_max + pad * 0.5,
        layer["material"],
        ha="center",
        va="bottom",
        fontsize=9,
        rotation=0 if layer["thickness"] / interface_x[-1] > 0.15 else 90,
    )

# Linear profile within each layer = straight lines between interface points
ax.plot(interface_x, interface_temperatures, color="crimson", linewidth=3, marker="o")

for x, T in zip(interface_x, interface_temperatures):
    ax.annotate(
        f"{T:.1f} °C",
        (x, T),
        textcoords="offset points",
        xytext=(6, 6),
        fontsize=9,
    )

ax.set_xlim(0, interface_x[-1])
ax.set_ylim(T_min - pad, T_max + 3 * pad)
ax.set_xlabel("Position through wall (m)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Temperature Distribution in Composite Wall")
ax.grid(True, alpha=0.4)

st.pyplot(fig)
plt.close(fig)

# --------------------------------------------------
# FORMULAS
# --------------------------------------------------

st.divider()
st.header("📚 Governing Equations")

st.latex(r"R_i = \frac{L_i}{k_i A}")
st.latex(r"R_{total} = \sum_{i=1}^{n} R_i")
st.latex(r"Q = \frac{T_{hot}-T_{cold}}{R_{total}}")
st.latex(r"q'' = \frac{Q}{A}")
st.latex(r"U = \frac{1}{R_{total} A}")
st.latex(r"T_{i+1} = T_i - Q R_i")

st.info(
    "Assumptions: steady-state conduction, one-dimensional heat flow, "
    "constant thermal conductivity, no internal heat generation, "
    "and perfect thermal contact between layers. Material k values are "
    "typical room-temperature figures; check a data sheet for design work."
)


# Team Information
st.divider()

team_details = """
**Group:** 3 | **Members:** Pratham Patel, Karan Vora

**Pratham Patel**  
(25012250610041)  
Diploma in Information Technology (Sem 3) | **Institution:** LJ Polytechnic

**Karan Vora**  
(25012250610043)  
Diploma in Information Technology (Sem 3) | **Institution:** LJ Polytechnic

**Project:** 1D Composite Wall Heat Transfer Calculator  
**Team Name:** TrickMasters_DG
"""

st.markdown(team_details)
