[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17563763.svg)](https://doi.org/10.5281/zenodo.17563763)

# Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana

## Authors
- Mohamed Rami Mahmoud (National Water Research Center, Egypt)
- Luis A. Garcia (University of Vermont, USA)  
- Ahmed Medhat (National Water Research Center, Egypt)
- Mostafa Aboelkhear (University of Bologna, Italy)

## Abstract
This repository contains the Google Earth Engine (GEE) code for our 11-year (2013-2024) remote sensing assessment of water hyacinth invasion dynamics in Lake Tana, Ethiopia. The code implements our novel environmental coherence framework to evaluate multi-sensor algorithms using Landsat 8/9, Sentinel-1, and Sentinel-2 data.

## Paper Citation
Mahmoud, M.R., Garcia, L.A., Medhat, A., & Aboelkhear, M. (2025). Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana. 

## Requirements
- Google Earth Engine account (free at https://earthengine.google.com)
- Web browser with internet connection

## Data Sources
- Landsat 8/9 Surface Reflectance (2013-2024)
- Sentinel-2 MSI Surface Reflectance (2016-2024)
- Sentinel-1 SAR GRD (2014-2024)
- CHIRPS precipitation data
- ERA5-Land climate reanalysis
- Lake Tana water level from Hydroweb

## Code Structure
LakeTana-by-FAI-NDVI-SWIR-Sentinel.py
LakeTana-by-HybridFusion-Radar+Optical-Fusion-FAI+NDVI+SWIR.py
LakeTana-Evapotranspiration.py
LakeTana-FAI-Landsat.py
LakeTana-FAI-Sentinel.py
LakeTana-NDVI-FAI-Landsat.py
LakeTana-NDVI-FAI-Sentinel-Export-Image-for-2019-Nov.py
LakeTana-NDVI-FAI-Sentinel.py
LakeTana-NDVI-Landsat.py
LakeTana-NDVI-Sentinel.py
LakeTana-NDWI-FAI-Landsat.py
LakeTana-NDWI-FAI-Sentinel.py
LakeTana-Radar-Sentinel-1.py
LakeTana-Rainfall-CHIRPS.py
LakeTana-Temperature-and-Humidity.py
LakeTana-Water-Level-using-hydroweb-monthly.py
README.md
Results-In-Excel-Sheets.zip


## Key Findings
- Sentinel-2 NDVI and NDVI+FAI achieved perfect environmental coherence scores (1.000)
- Peak infestation period: 2018-2019 (>13 km²)
- Recent resurgence: 68.7% increase from 2022 to 2024

## How to Run
1. Open Google Earth Engine Code Editor: https://code.earthengine.google.com
2. Copy the code from this repository
3. Set your study area to Lake Tana (coordinates: 12.0°N, 37.3°E)
4. Run the scripts in the order listed above
5. Results will display in the console and map panels

## Contact
For questions about this code, contact: mohamed_rami@nwrc.gov.eg

## License
MIT License - See LICENSE file for details
```
