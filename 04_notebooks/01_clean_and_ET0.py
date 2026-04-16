# ============================================================
# Script 1: NASA Power Data Cleaning + FAO-56 ET0
# Project: Irrigation_DSS_Soybean
# Location: Starkville, Mississippi (lat=33.8711, lon=-89.0592)
# Author: AnithaM55 | Date: 2026-04-15
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os

print("=" * 55)
print("Script 1: NASA Power Cleaning + FAO-56 ET0")
print("Location: Starkville, Mississippi 2025")
print("=" * 55)

# ── 1. Load NASA Power 2025 data ─────────────────────────────
print("\nStep 1: Loading NASA Power data...")

df = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\01_raw_data\weather\2025_Weather _NASA Power Mississippi.csv",
    skiprows=13,
    na_values=["-999", -999]
)

print("Columns found:", df.columns.tolist())
print("Total rows:", len(df))
print(df.head())

# ── 2. Rename columns ────────────────────────────────────────
print("\nStep 2: Renaming columns...")
df = df.rename(columns={
    "YEAR"              : "year",
    "DOY"               : "doy",
    "ALLSKY_SFC_SW_DWN" : "solar_rad",
    "T2M_MAX"           : "Tmax_C",
    "T2M_MIN"           : "Tmin_C",
    "PRECTOTCORR"       : "precip_mm",
    "WS2M"              : "wind_speed"
})

# ── 3. Convert DOY to date ───────────────────────────────────
print("\nStep 3: Converting DOY to date...")
df["date"] = pd.to_datetime(
    df["year"].astype(str) +
    df["doy"].astype(str).str.zfill(3),
    format="%Y%j"
)
df["Tmean_C"] = (df["Tmax_C"] + df["Tmin_C"]) / 2
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# ── 4. QC flags ──────────────────────────────────────────────
print("\nStep 4: Running QC checks...")
df["QC_flag"] = 0
df.loc[df["Tmax_C"]     >  50, "QC_flag"] = 1
df.loc[df["Tmin_C"]     < -30, "QC_flag"] = 1
df.loc[df["precip_mm"]  <   0, "QC_flag"] = 1
df.loc[df["solar_rad"]  <   0, "QC_flag"] = 1
df.loc[df["wind_speed"] <   0, "QC_flag"] = 1
print(f"Total rows    : {len(df)}")
print(f"Flagged rows  : {df['QC_flag'].sum()}")
print(f"Missing values:\n{df.isnull().sum()}")

# ── 5. FAO-56 Penman-Monteith ET0 ────────────────────────────
print("\nStep 5: Computing FAO-56 ET0...")

lat_rad   = 33.8711 * math.pi / 180
elevation = 95.93

def compute_ET0(row):
    try:
        T    = row["Tmean_C"]
        Tmax = row["Tmax_C"]
        Tmin = row["Tmin_C"]
        Rs   = row["solar_rad"]
        u2   = row["wind_speed"]
        doy  = row["doy"]
        if any(pd.isna([T, Tmax, Tmin, Rs, u2])):
            return np.nan
        # Saturation vapour pressure
        es    = 0.6108 * math.exp(17.27 * T / (T + 237.3))
        ea    = 0.6108 * math.exp(17.27 * Tmin / (Tmin + 237.3))
        delta = 4098 * es / (T + 237.3) ** 2
        # Psychrometric constant
        P     = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26
        gamma = 0.000665 * P
        # Extraterrestrial radiation
        dr    = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
        decl  = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
        ws    = math.acos(-math.tan(lat_rad) * math.tan(decl))
        Ra    = (24 * 60 / math.pi) * 0.0820 * dr * (
                    ws * math.sin(lat_rad) * math.sin(decl) +
                    math.cos(lat_rad) * math.cos(decl) * math.sin(ws)
                )
        # Net radiation
        Rns   = 0.77 * Rs
        Rnl   = 4.903e-9 * (
                    (Tmax + 273.16) ** 4 +
                    (Tmin + 273.16) ** 4
                ) / 2 * (0.34 - 0.14 * math.sqrt(max(ea, 0))) * \
                (1.35 * Rs / (0.75 * Ra + 0.0001) - 0.35)
        Rn    = Rns - Rnl
        # FAO-56 ET0
        ET0   = (0.408 * delta * (Rn - 0) +
                 gamma * (900 / (T + 273)) * u2 * (es - ea)) / \
                (delta + gamma * (1 + 0.34 * u2))
        return round(max(ET0, 0), 3)
    except:
        return np.nan

df["ET0_mm"] = df.apply(compute_ET0, axis=1)
print(f"ET0 computed for {df['ET0_mm'].notna().sum()} days")

# ── 6. Filter growing season April - October ─────────────────
print("\nStep 6: Filtering growing season Apr-Oct...")
growing = df[
    (df["date"].dt.month >= 4) &
    (df["date"].dt.month <= 10)
].copy()
print(f"Growing season rows: {len(growing)}")

# ── 7. Monthly summary ───────────────────────────────────────
print("\n── Monthly Summary ──")
growing["month"] = growing["date"].dt.month
monthly = growing.groupby("month").agg(
    days      = ("date",     "count"),
    ET0_mean  = ("ET0_mm",   "mean"),
    ET0_total = ("ET0_mm",   "sum"),
    Tmax_mean = ("Tmax_C",   "mean"),
    precip    = ("precip_mm","sum")
).round(2)
monthly.index = monthly.index.map({
    4:"April", 5:"May",    6:"June",
    7:"July",  8:"August", 9:"September",
    10:"October"
})
print(monthly.to_string())

# ── 8. Save outputs ──────────────────────────────────────────
print("\nStep 7: Saving outputs...")
out = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\et0_computed"
os.makedirs(out, exist_ok=True)

df.to_csv(
    os.path.join(out, "2025_ET0_full_year.csv"),
    index=False
)
growing.to_csv(
    os.path.join(out, "2025_ET0_growing_season.csv"),
    index=False
)
print("  Saved: 2025_ET0_full_year.csv")
print("  Saved: 2025_ET0_growing_season.csv")

# ── 9. Plots ─────────────────────────────────────────────────
print("\nStep 8: Creating plots...")
viz = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\05_visualizations"
os.makedirs(viz, exist_ok=True)

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

# Plot 1: ET0
ax1.plot(growing["date"], growing["ET0_mm"],
         color="orange", linewidth=1.2, label="ET0 (mm/day)")
ax1.set_title("FAO-56 Reference ET0 — Mississippi 2025 Growing Season")
ax1.set_ylabel("ET0 (mm/day)")
ax1.legend()
ax1.grid(alpha=0.3)

# Plot 2: Temperature
ax2.plot(growing["date"], growing["Tmax_C"],
         color="red",  linewidth=1, label="Tmax (°C)")
ax2.plot(growing["date"], growing["Tmin_C"],
         color="blue", linewidth=1, label="Tmin (°C)")
ax2.set_title("Daily Temperature — Mississippi 2025 Growing Season")
ax2.set_ylabel("Temperature (°C)")
ax2.legend()
ax2.grid(alpha=0.3)

# Plot 3: Precipitation
ax3.bar(growing["date"], growing["precip_mm"],
        color="steelblue", alpha=0.7, label="Precipitation (mm)")
ax3.set_title("Daily Precipitation — Mississippi 2025 Growing Season")
ax3.set_ylabel("Precipitation (mm)")
ax3.set_xlabel("Date")
ax3.legend()
ax3.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(
    os.path.join(viz, "ET0_temperature_precipitation_2025.png"),
    dpi=150
)
plt.show()
print("  Plot saved: ET0_temperature_precipitation_2025.png")

print("\n" + "=" * 55)
print("✓ Script 1 complete!")
print("Next: run 02_dynamic_Kc.py")
print("=" * 55)