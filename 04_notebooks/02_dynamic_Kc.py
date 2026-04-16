# ============================================================
# Script 2: Dynamic Kc + ETc Computation
# Project: Irrigation_DSS_Soybean
# Location: Starkville, Mississippi 2025
# Author: AnithaM55 | Date: 2026-04-15
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

print("=" * 55)
print("Script 2: Dynamic Kc + ETc Computation")
print("Location: Starkville, Mississippi 2025")
print("=" * 55)

# ── 1. Load ET0 data ─────────────────────────────────────────
print("\nStep 1: Loading ET0 data...")
et0 = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\et0_computed\2025_ET0_growing_season.csv"
)
et0["date"] = pd.to_datetime(et0["date"])
print(f"ET0 rows loaded: {len(et0)}")
print(f"Date range: {et0['date'].min()} to {et0['date'].max()}")

# ── 2. Load MODIS ETa daily data ─────────────────────────────
print("\nStep 2: Loading MODIS ETa daily data...")
modis = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\et0_computed\2025_MODIS_ETa_daily.csv"
)
modis["date"] = pd.to_datetime(modis["date"])
print(f"MODIS ETa rows loaded: {len(modis)}")
print(f"Date range: {modis['date'].min()} to {modis['date'].max()}")

# ── 3. Merge ET0 with MODIS ETa ───────────────────────────────
print("\nStep 3: Merging ET0 with MODIS ETa...")
et0   = et0.sort_values("date")
modis = modis.sort_values("date")

merged = pd.merge_asof(
    et0,
    modis[["date","ETa_mm_day","ETa_mm_8day"]],
    on="date",
    direction="nearest",
    tolerance=pd.Timedelta("8D")
)
print(f"Merged rows: {len(merged)}")
print(merged[["date","ET0_mm","ETa_mm_day"]].head(10).to_string())

# ── 4. Compute dynamic Kc ─────────────────────────────────────
print("\nStep 4: Computing dynamic Kc...")
merged["Kc_dynamic"] = (
    merged["ETa_mm_day"] / merged["ET0_mm"]
).round(3)
merged["Kc_dynamic"] = merged["Kc_dynamic"].clip(0, 1.5)

# ── 5. Assign FAO-56 growth stage ────────────────────────────
print("\nStep 5: Assigning growth stages...")
stages = pd.read_csv(
    r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\01_raw_data\crop_stages\soybean_stages_FAO56.csv"
)
print("Crop stages loaded:")
print(stages[["growth_stage","stage_start_date",
              "stage_end_date","Kc_FAO56"]].to_string())

def assign_stage(date):
    for _, row in stages.iterrows():
        start = pd.to_datetime(row["stage_start_date"])
        end   = pd.to_datetime(row["stage_end_date"])
        if start <= date <= end:
            return row["growth_stage"], row["Kc_FAO56"]
    return "Outside season", np.nan

merged[["growth_stage","Kc_FAO56"]] = merged["date"].apply(
    lambda d: pd.Series(assign_stage(d))
)

# ── 6. Compute ETc ────────────────────────────────────────────
merged["ETc_mm"] = (
    merged["Kc_dynamic"] * merged["ET0_mm"]
).round(3)

print("\nSample output:")
print(merged[["date","ET0_mm","ETa_mm_day",
              "Kc_dynamic","Kc_FAO56",
              "growth_stage","ETc_mm"]].head(20).to_string())

# ── 7. Summary by growth stage ────────────────────────────────
print("\n── Summary by Growth Stage ──")
season = merged[merged["growth_stage"] != "Outside season"]
summary = season.groupby("growth_stage").agg(
    days         = ("date",       "count"),
    ET0_mean     = ("ET0_mm",     "mean"),
    ETa_mean     = ("ETa_mm_day", "mean"),
    Kc_dynamic   = ("Kc_dynamic", "mean"),
    Kc_FAO56     = ("Kc_FAO56",   "mean"),
    ETc_total_mm = ("ETc_mm",     "sum")
).round(2)
print(summary.to_string())

# ── 8. Save output ────────────────────────────────────────────
print("\nStep 6: Saving outputs...")
out = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\02_processed\kc_dynamic"
os.makedirs(out, exist_ok=True)

merged.to_csv(
    os.path.join(out, "2025_Kc_dynamic_Mississippi.csv"),
    index=False
)
print("  Saved: 2025_Kc_dynamic_Mississippi.csv")

# ── 9. Plots ─────────────────────────────────────────────────
print("\nStep 7: Creating plots...")
viz = r"C:\Users\Anith\Documents\Irrigation_DSS_Soybean\05_visualizations"

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

# Plot 1: ET0 vs ETa vs ETc
ax1.plot(merged["date"], merged["ET0_mm"],
         color="orange", linewidth=1, label="ET0 (mm/day)", alpha=0.8)
ax1.plot(merged["date"], merged["ETa_mm_day"],
         color="blue", linewidth=1.5, label="ETa MODIS (mm/day)")
ax1.plot(merged["date"], merged["ETc_mm"],
         color="green", linewidth=1, label="ETc (mm/day)",
         linestyle="--", alpha=0.8)
ax1.set_title("ET0 vs ETa (MODIS) vs ETc — Mississippi Soybean 2025")
ax1.set_ylabel("mm/day")
ax1.legend()
ax1.grid(alpha=0.3)

# Plot 2: Dynamic Kc vs FAO-56 Kc
colors = {
    "Initial"     : "green",
    "Development" : "orange",
    "Mid-Season"  : "blue",
    "Late-Season" : "red"
}
for stage, grp in merged.groupby("growth_stage"):
    if stage == "Outside season":
        continue
    color = colors.get(stage, "gray")
    ax2.scatter(grp["date"], grp["Kc_dynamic"],
                color=color, s=8, label=f"{stage} (dynamic)", alpha=0.7)
ax2.plot(merged["date"], merged["Kc_FAO56"],
         color="black", linewidth=2, linestyle="--",
         label="FAO-56 Kc standard")
ax2.set_title("Dynamic Kc vs FAO-56 Kc — Mississippi Soybean 2025")
ax2.set_ylabel("Kc")
ax2.legend(loc="upper right", fontsize=8)
ax2.grid(alpha=0.3)

# Plot 3: Monthly ETc total
merged["month"] = merged["date"].dt.month
monthly_etc = season.groupby(
    season["date"].dt.month
)["ETc_mm"].sum().round(1)
month_names = {
    4:"Apr", 5:"May", 6:"Jun", 7:"Jul",
    8:"Aug", 9:"Sep", 10:"Oct"
}
monthly_etc.index = monthly_etc.index.map(month_names)
ax3.bar(monthly_etc.index, monthly_etc.values,
        color="steelblue", alpha=0.8)
ax3.set_title("Monthly Total ETc — Mississippi Soybean 2025")
ax3.set_ylabel("ETc (mm/month)")
ax3.set_xlabel("Month")
for i, v in enumerate(monthly_etc.values):
    ax3.text(i, v + 2, str(v), ha="center", fontsize=9)
ax3.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(
    os.path.join(viz, "Kc_ETc_analysis_2025.png"),
    dpi=150
)
plt.show()
print("  Plot saved: Kc_ETc_analysis_2025.png")

print("\n" + "=" * 55)
print("✓ Script 2 complete!")
print("Next: run 03_irrigation_scheduling.py")
print("=" * 55)