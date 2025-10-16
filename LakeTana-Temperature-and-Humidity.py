# Research Project: Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana
# Authours: Mohamed Rami Mahmoud , Luis A. Garcia , Ahmed Medhat  and Mostafa Aboelkhear  
# Developer: Prof. Mohamed Rami Mahmoud (ORCID: http://orcid.org/0000-0002-3393-987X)
# Contact: ORCID: http://orcid.org/0000-0002-3393-987X
# Version: <v1.0> | Date: <2025-10-16>


import ee
import pandas as pd
import datetime
import calendar
import geopandas as gpd
from google.colab import drive, files

# Install required packages
!pip install earthengine-api geopandas --quiet

# Mount Google Drive
drive.mount('/content/drive')

# Authenticate and initialize Earth Engine
try:
    ee.Initialize(project='Your-Project-ID')
    print('Earth Engine initialized with project ee-rami-02')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='Your-Project-ID')

# Load study area shapefile
area_shp_path = '/content/drive/MyDrive/shp/Area_of_study_Bigger.shp'
area_gdf = gpd.read_file(area_shp_path)

def gdf_to_fc(gdf):
    import json
    geojson = json.loads(gdf.to_json())
    features = [ee.Feature(ee.Geometry(f['geometry'])) for f in geojson['features']]
    return ee.FeatureCollection(features)

area_fc = gdf_to_fc(area_gdf)
area_geom = area_fc.geometry()

# Years and months of interest
years = list(range(2013, 2025))  # 2013 to 2024 inclusive
months = [10, 11, 12]  # October, November, December

# Define variables and units
variables = [
    ('Temperature_Air_2m_Max_24h', 'Temperature Max', '°C', lambda x: x - 273.15),
    ('Temperature_Air_2m_Min_24h', 'Temperature Min', '°C', lambda x: x - 273.15),
    ('Temperature_Air_2m_Mean_24h', 'Temperature Mean', '°C', lambda x: x - 273.15),
    ('Specific_Humidity_2m_Mean', 'Specific Humidity', 'kg/kg', lambda x: x),
    ('Relative_Humidity_2m_06h', 'Relative Humidity (06h)', '%', lambda x: x),
    ('Relative_Humidity_2m_15h', 'Relative Humidity (15h)', '%', lambda x: x)
]

results = []

for year in years:
    for month in months:
        first_day = datetime.date(year, month, 1)
        last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
        
        # Load daily AgERA5 images
        agera5 = ee.ImageCollection('projects/climate-engine-pro/assets/ce-ag-era5/daily') \
            .filterDate(first_day.isoformat(), last_day.isoformat()) \
            .filterBounds(area_geom)
        
        print(f"\nProcessing {year}-{month:02d}")
        
        for band, var_name, unit, convert_func in variables:
            try:
                # Compute statistics
                min_val = agera5.select(band).min().reduceRegion(
                    reducer=ee.Reducer.min(),
                    geometry=area_geom,
                    scale=10000,
                    maxPixels=1e13
                ).get(band)
                
                max_val = agera5.select(band).max().reduceRegion(
                    reducer=ee.Reducer.max(),
                    geometry=area_geom,
                    scale=10000,
                    maxPixels=1e13
                ).get(band)
                
                mean_val = agera5.select(band).mean().reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=area_geom,
                    scale=10000,
                    maxPixels=1e13
                ).get(band)
                
                # Convert and format values
                min_val = convert_func(min_val.getInfo()) if min_val else None
                max_val = convert_func(max_val.getInfo()) if max_val else None
                mean_val = convert_func(mean_val.getInfo()) if mean_val else None
                
                # Print values
                print(f"  {var_name} ({unit}):")
                print(f"    Min: {min_val:.2f} {unit}")
                print(f"    Max: {max_val:.2f} {unit}")
                print(f"    Avg: {mean_val:.2f} {unit}")
                
                # Store results
                results.append({
                    'Year': year,
                    'Month': month,
                    'Variable': f"{var_name} ({unit})",
                    'Min': min_val,
                    'Max': max_val,
                    'Mean': mean_val
                })
                
            except Exception as e:
                print(f"Error processing {var_name}: {str(e)}")
                results.append({
                    'Year': year,
                    'Month': month,
                    'Variable': f"{var_name} ({unit})",
                    'Min': None,
                    'Max': None,
                    'Mean': None
                })

# Create DataFrame
df = pd.DataFrame(results)

# Save to Excel
excel_path = '/content/drive/MyDrive/Lake_Tana_Climate_2013-2024.xlsx'
df.to_excel(excel_path, index=False)

# Download locally
local_path = 'Lake_Tana_Climate_2013-2024.xlsx'
df.to_excel(local_path, index=False)
files.download(local_path)

print(f"Results saved to {excel_path}")
