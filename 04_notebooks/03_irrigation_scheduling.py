# ============================================================
# Script 3: Water Balance + Irrigation Scheduling
# Project: Irrigation_DSS_Soybean
# Location: Starkville, Mississippi 2025
# Author: AnithaM55 | Date: 2026-04-15
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

print("=" * 55)
print("Script 3: Water Balance + Irrigation Scheduling")
print("Location: Starkville, Mississippi 2025")
print("=" * 55)

# ── 1. Load Kc + ET data ──────────────────────────────────────
print("\nStep 1: Loading Kc and ET data...")
df = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\kc_dynamic\2025_Kc_dynamic_Mississippi.csv"
)
df["date"] = pd.to_datetime(df["date"])
df = df[df["growth_stage"] != "Outside season"].copy()
df = df.sort_values("date").reset_index(drop=True)
print(f"Growing season rows: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# ── 2. Soil parameters Mississippi sandy loam ─────────────────
print("\nStep 2: Setting soil parameters...")
field_capacity_mm = 80.0
wilting_point_mm  = 30.0
available_water   = field_capacity_mm - wilting_point_mm
MAD               = 0.50
RAW               = available_water * MAD
print(f"Field capacity : {field_capacity_mm} mm")
print(f"Wilting point  : {wilting_point_mm} mm")
print(f"Available water: {available_water} mm")
print(f"RAW trigger    : {RAW} mm")

# ── 3. Daily water balance ────────────────────────────────────
print("\nStep 3: Running daily water balance...")
soil_water = field_capacity_mm
results    = []
total_irr  = 0
irr_events = 0

for _, row in df.iterrows():
    ETc    = row["ETc_mm"]    if not pd.isna(row["ETc_mm"])    else 0
    precip = row["precip_mm"] if not pd.isna(row["precip_mm"]) else 0
    stage  = row["growth_stage"]

    soil_water = soil_water + precip - ETc

    if soil_water > field_capacity_mm:
        drainage   = soil_water - field_capacity_mm
        soil_water = field_capacity_mm
    else:
        drainage = 0

    deficit = max(0, field_capacity_mm - soil_water)

    if deficit >= RAW:
        irrigation = deficit
        soil_water = field_capacity_mm
        total_irr += irrigation
        irr_events += 1
    else:
        irrigation = 0

    results.append({
        "date"                     : row["date"],
        "growth_stage"             : stage,
        "ETc_mm"                   : round(ETc, 3),
        "precip_mm"                : round(precip, 3),
        "soil_water_mm"            : round(soil_water, 3),
        "soil_water_deficit_mm"    : round(deficit, 3),
        "drainage_mm"              : round(drainage, 3),
        "irrigation_recommended_mm": round(irrigation, 3)
    })

out_df = pd.DataFrame(results)
print(f"Total irrigation events: {irr_events}")
print(f"Total irrigation (mm)  : {round(total_irr, 1)}")
print(f"Total ETc (mm)         : {round(out_df['ETc_mm'].sum(), 1)}")
print(f"Total precip (mm)      : {round(out_df['precip_mm'].sum(), 1)}")

# ── 4. Summary by growth stage ────────────────────────────────
print("\n── Summary by Growth Stage ──")
summary = out_df.groupby("growth_stage").agg(
    days         = ("date",                      "count"),
    ETc_total    = ("ETc_mm",                    "sum"),
    precip_total = ("precip_mm",                 "sum"),
    irr_total    = ("irrigation_recommended_mm", "sum"),
    irr_events   = ("irrigation_recommended_mm",
                    lambda x: (x > 0).sum()),
    deficit_mean = ("soil_water_deficit_mm",     "mean")
).round(2)
print(summary.to_string())

# ── 5. Monthly summary ────────────────────────────────────────
print("\n── Monthly Irrigation Summary ──")
out_df["month"] = out_df["date"].dt.month
monthly = out_df.groupby("month").agg(
    ETc_mm        = ("ETc_mm",                    "sum"),
    precip_mm     = ("precip_mm",                 "sum"),
    irrigation_mm = ("irrigation_recommended_mm", "sum"),
    irr_events    = ("irrigation_recommended_mm",
                     lambda x: (x > 0).sum())
).round(1)
monthly.index = monthly.index.map({
    4:"April", 5:"May",    6:"June",
    7:"July",  8:"August", 9:"September",
    10:"October"
})
print(monthly.to_string())

# ── 6. Save output ────────────────────────────────────────────
print("\nStep 4: Saving outputs...")
out_path = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\irrigation_scheduling"
os.makedirs(out_path, exist_ok=True)
out_df.to_csv(
    os.path.join(out_path,
                 "2025_irrigation_schedule_Mississippi.csv"),
    index=False
)
print("  Saved: 2025_irrigation_schedule_Mississippi.csv")

# ── 7. Plots ─────────────────────────────────────────────────
print("\nStep 5: Creating plots...")
viz = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\05_visualizations"
os.makedirs(viz, exist_ok=True)

fig, axes = plt.subplots(4, 1, figsize=(12, 14))

# Plot 1: Soil water content
axes[0].plot(out_df["date"], out_df["soil_water_mm"],
             color="blue", linewidth=1.2,
             label="Soil water (mm)")
axes[0].axhline(y=field_capacity_mm, color="green",
                linestyle="--", alpha=0.7,
                label=f"Field capacity ({field_capacity_mm}mm)")
axes[0].axhline(y=wilting_point_mm, color="red",
                linestyle="--", alpha=0.7,
                label=f"Wilting point ({wilting_point_mm}mm)")
axes[0].axhline(y=field_capacity_mm - RAW, color="orange",
                linestyle="--", alpha=0.7,
                label=f"Irrigation trigger ({field_capacity_mm-RAW}mm)")
axes[0].set_title(
    "Soil Water Content — Mississippi Soybean 2025")
axes[0].set_ylabel("Soil water (mm)")
axes[0].legend(fontsize=8)
axes[0].grid(alpha=0.3)

# Plot 2: Precipitation vs irrigation events
irr_days = out_df[out_df["irrigation_recommended_mm"] > 0]
axes[1].bar(out_df["date"], out_df["precip_mm"],
            color="steelblue", alpha=0.6,
            label="Precipitation (mm)")
axes[1].bar(irr_days["date"],
            irr_days["irrigation_recommended_mm"],
            color="red", alpha=0.8,
            label="Irrigation (mm)")
axes[1].set_title(
    "Precipitation vs Irrigation Events — Mississippi 2025")
axes[1].set_ylabel("mm")
axes[1].legend()
axes[1].grid(alpha=0.3)

# Plot 3: Soil water deficit
axes[2].fill_between(out_df["date"],
                     out_df["soil_water_deficit_mm"],
                     alpha=0.5, color="orange",
                     label="Soil water deficit (mm)")
axes[2].axhline(y=RAW, color="red", linestyle="--",
                label=f"Irrigation trigger ({RAW}mm)")
axes[2].set_title(
    "Soil Water Deficit — Mississippi Soybean 2025")
axes[2].set_ylabel("Deficit (mm)")
axes[2].legend()
axes[2].grid(alpha=0.3)

# Plot 4: Monthly water balance ── FIXED ──────────────────────
out_df["month"] = out_df["date"].dt.month
monthly_etc = out_df.groupby("month")["ETc_mm"].sum()
monthly_pcp = out_df.groupby("month")["precip_mm"].sum()
monthly_irr = out_df.groupby(
    "month")["irrigation_recommended_mm"].sum()

all_months  = sorted(set(monthly_etc.index) |
                     set(monthly_pcp.index) |
                     set(monthly_irr.index))
month_label = {4:"Apr", 5:"May", 6:"Jun", 7:"Jul",
               8:"Aug", 9:"Sep", 10:"Oct"}
month_names = [month_label[m] for m in all_months]
etc_vals    = [monthly_etc.get(m, 0) for m in all_months]
pcp_vals    = [monthly_pcp.get(m, 0) for m in all_months]
irr_vals    = [monthly_irr.get(m, 0) for m in all_months]

x     = np.arange(len(all_months))
width = 0.25
axes[3].bar(x - width, etc_vals,
            width, color="orange",
            alpha=0.8, label="ETc (mm)")
axes[3].bar(x, pcp_vals,
            width, color="steelblue",
            alpha=0.8, label="Precipitation (mm)")
axes[3].bar(x + width, irr_vals,
            width, color="red",
            alpha=0.8, label="Irrigation (mm)")
axes[3].set_xticks(x)
axes[3].set_xticklabels(month_names)
axes[3].set_title(
    "Monthly Water Balance — Mississippi Soybean 2025")
axes[3].set_ylabel("mm")
axes[3].set_xlabel("Month")
axes[3].legend()
axes[3].grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(
    os.path.join(viz, "irrigation_scheduling_2025.png"),
    dpi=150
)
plt.show()
print("  Plot saved: irrigation_scheduling_2025.png")

print("\n" + "=" * 55)
print("✓ Script 3 complete!")
print("Next: run 04_final_visualizations.py")
print("=" * 55)