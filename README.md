\# Irrigation\_DSS\_Soybean

\## ABE 6933 — Comprehensive Data Management in Agriculture, Spring 2025



\*\*Author:\*\* AnithaM55  

\*\*Date created:\*\* 2026-04-12  

\*\*Last modified:\*\* 2026-04-12  



\---



\## Description



Soybean production in the southeastern United States is highly sensitive to

water availability. Traditional irrigation scheduling based on static crop

coefficients and generalized weather data fails to capture field-level

variability. This project integrates MODIS-derived actual evapotranspiration

(MOD16A2GF), NOAA weather data, and the FAO-56 Penman-Monteith framework to

dynamically estimate crop water demand and generate irrigation scheduling

outputs. A structured relational database and reproducible Python workflow

are implemented in accordance with FAIR data principles.



\---



\## Data types

\- Observational: `.csv`

\- Remote sensing: `.hdf`, `.tif`

\- Derived outputs: `.csv`, `.xlsx`

\- Visualizations: `.png`, `.html`

\- Notebooks: `.ipynb`



\---



\## Repository structure



&#x20;   Irrigation\_DSS\_Soybean/

&#x20;   01\_raw\_data/

&#x20;       weather/               # Daily NOAA weather CSV files

&#x20;       modis\_et/              # MODIS MOD16A2GF HDF/GeoTIFF tiles

&#x20;       crop\_stages/           # Soybean phenology reference tables

&#x20;   02\_processed/

&#x20;       et0\_computed/          # FAO-56 ET0 outputs

&#x20;       kc\_dynamic/            # Derived Kc time series (ETa/ET0)

&#x20;       irrigation\_scheduling/ # Water deficit and recommendations

&#x20;   03\_database/               # SQLite .db file and SQL schema scripts

&#x20;   04\_notebooks/              # Jupyter Notebooks (.ipynb)

&#x20;   05\_visualizations/         # Charts (.png) and dashboards (.html)

&#x20;   06\_metadata/               # README files and metadata sheets (.csv)

&#x20;   README.md



\---



\## Data sources



| Dataset | Source | Format | License |

|---------|--------|--------|---------|

| Daily weather | NOAA GHCN-Daily | .csv | Public domain |

| Actual ET | NASA MODIS MOD16A2GF v061 | .hdf / .tif | Open with attribution |

| Reference ET0 | FAO-56 Penman-Monteith (computed) | .csv | — |

| Crop stages | USDA / published soybean trials | .csv | Public domain |



\---



\## How to reproduce



1\. Clone this repository

2\. Install dependencies: `pip install -r requirements.txt`

3\. Run notebooks in order inside `04\_notebooks/`

4\. Outputs are written to `02\_processed/` and `05\_visualizations/`



\---



\## License

Data: CC0-1.0  

Code: CC0-1.0  



\---



\## Citation

AnithaM55 (2026). Irrigation Decision Support System for Soybean — ABE 6933

Course Project. Mississippi State University.

https://github.com/AnithaM55/Irrigation\_DSS\_Soybean

