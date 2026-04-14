# ============================================================
# Script 1: NASA Power Data Cleaning + FAO-56 ET0 Computation
# Project: Irrigation_DSS_Soybean
# Location: Mississippi (lat=33.8711, lon=-89.0592)
# Author: AnithaM55
# Date: 2026-04-14
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os

# ── 1. Load NASA Power CSV (skip header rows 1-13) ──────────
print("Loading NASA Power data...")

df = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\01_raw_data\weather\2025_Weather _NASA Power Mississippi.csv",
    skiprows=13,
    na_values=["-999", -999]
)

print("Columns found:", df.columns.tolist())
print("Total rows:", len(df))
print(df.head())

# ── 2. Rename columns ────────────────────────────────────────
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
df["date"] = pd.to_datetime(
    df["year"].astype(str) + df["doy"].astype(str).str.zfill(3),
    format="%Y%j"
)

# ── 4. Mean temperature ──────────────────────────────────────
df["Tmean_C"] = (df["Tmax_C"] + df["Tmin_C"]) / 2

# ── 5. QC Flags ──────────────────────────────────────────────
print("\n── QC Check ──")
print("Missing values:\n", df.isnull().sum())

df["QC_flag"] = 0
df.loc[df["Tmax_C"]    >  50, "QC_flag"] = 1
df.loc[df["Tmin_C"]    < -30, "QC_flag"] = 1
df.loc[df["precip_mm"] <   0, "QC_flag"] = 1
df.loc[df["solar_rad"] <   0, "QC_flag"] = 1
df.loc[df["wind_speed"]<   0, "QC_flag"] = 1
print(f"Flagged rows: {df['QC_flag'].sum()}")

# ── 6. FAO-56 ET0 ────────────────────────────────────────────
print("\nComputing FAO-56 ET0...")

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
        dr   = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
        decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
        ws   = math.acos(-math.tan(lat_rad) * math.tan(decl))
        Ra   = (24 * 60 / math.pi) * 0.0820 * dr * (
                   ws * math.sin(lat_rad) * math.sin(decl) +
                   math.cos(lat_rad) * math.cos(decl) * math.sin(ws)
               )

        # Net radiation
        Rns  = 0.77 * Rs
        Rnl  = 4.903e-9 * ((Tmax+273.16)**4 + (Tmin+273.16)**4) / 2 * \
               (0.34 - 0.14 * math.sqrt(ea)) * \
               (1.35 * Rs / (0.75 * Ra + 0.0001) - 0.35)
        Rn   = Rns - Rnl

        # ET0 mm/day
        ET0  = (0.408 * delta * (Rn - 0) +
                gamma * (900 / (T + 273)) * u2 * (es - ea)) / \
               (delta + gamma * (1 + 0.34 * u2))

        return round(max(ET0, 0), 3)
    except:
        return np.nan

df["ET0_mm"] = df.apply(compute_ET0, axis=1)
print(f"ET0 computed for {df['ET0_mm'].notna().sum()} days")
print(df[["date","Tmax_C","Tmin_C","solar_rad",
          "wind_speed","precip_mm","ET0_mm"]].head(10))

# ── 7. Filter growing season (April - October) ───────────────
growing = df[
    (df["date"].dt.month >= 4) &
    (df["date"].dt.month <= 10)
].copy()
print(f"\nGrowing season rows: {len(growing)}")

# ── 8. Save outputs ──────────────────────────────────────────
out_dir = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\et0_computed"
os.makedirs(out_dir, exist_ok=True)

df.to_csv(
    os.path.join(out_dir, "2025_ET0_full_year.csv"),
    index=False
)
growing.to_csv(
    os.path.join(out_dir, "2025_ET0_growing_season.csv"),
    index=False
)
print("Saved to 02_processed/et0_computed/")

# ── 9. Plot ET0 ──────────────────────────────────────────────
viz_dir = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\05_visualizations"
os.makedirs(viz_dir, exist_ok=True)

plt.figure(figsize=(12, 4))
plt.plot(growing["date"], growing["ET0_mm"],
         color="orange", linewidth=1.2, label="ET0 (mm/day)")
plt.title("FAO-56 Reference ET0 — Mississippi 2025 Growing Season")
plt.xlabel("Date")
plt.ylabel("ET0 (mm/day)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(viz_dir, "ET0_2025_growing_season.png"), dpi=150)
plt.show()
print("Plot saved!")

print("\n✓ Script 1 complete!")