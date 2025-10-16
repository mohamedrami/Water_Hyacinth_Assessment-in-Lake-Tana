# Research Project: Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana
# Authours: Mohamed Rami Mahmoud , Luis A. Garcia , Ahmed Medhat  and Mostafa Aboelkhear  
# Developer: Prof. Mohamed Rami Mahmoud (ORCID: http://orcid.org/0000-0002-3393-987X)
# Contact: ORCID: http://orcid.org/0000-0002-3393-987X
# Version: <v1.0> | Date: <2025-10-16>


import ee
import pandas as pd
import datetime
import calendar
from google.colab import drive, files

# Mount Google Drive
drive.mount('/content/drive')

# Authenticate and initialize Earth Engine
try:
    ee.Initialize(project='Your-Project-ID')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='Your-Project-ID')

# Load study area shapefile
import geopandas as gpd
area_shp_path = '/content/drive/MyDrive/shp/Area_of_study_Bigger.shp'
area_gdf = gpd.read_file(area_shp_path)

def gdf_to_fc(gdf):
    import json
    geojson = json.loads(gdf.to_json())
    features = [ee.Feature(ee.Geometry(f['geometry'])) for f in geojson['features']]
    return ee.FeatureCollection(features)

area_fc = gdf_to_fc(area_gdf)
area_geom = area_fc.geometry()

# Define years and months
years = list(range(2013, 2025))  # 2013 to 2024 inclusive
months = [10, 11, 12]  # October, November, December

results = []

for year in years:
    for month in months:
        first_day = datetime.date(year, month, 1)
        last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
        # Filter daily CHIRPS data for the month
        chirps_daily = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
        filtered = chirps_daily.filterDate(first_day.isoformat(), last_day.isoformat())
        # Sum precipitation over the month
        monthly_precip = filtered.select('precipitation').sum()
        # Calculate total precipitation over the study area
        total_precip = monthly_precip.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=area_geom,
            scale=5566,
            maxPixels=1e13
        ).get('precipitation')
        results.append({
            'Year': year,
            'Month': month,
            'Total mm per month': total_precip
        })

# Convert to DataFrame and download values from GEE
def get_value(val):
    try:
        return val.getInfo() if hasattr(val, 'getInfo') else val
    except:
        return None

df = pd.DataFrame(results)
df['Total mm per month'] = df['Total mm per month'].apply(get_value)

# Save to Excel in your Google Drive
excel_path = '/content/drive/MyDrive/Monthly_Rainfall_Tana_CHIRPS.xlsx'
df.to_excel(excel_path, index=False)

# Also save locally for download
local_path = 'Monthly_Rainfall_Tana_CHIRPS.xlsx'
df.to_excel(local_path, index=False)

# Download file
files.download(local_path)

print(f"Excel file saved to Google Drive at: {excel_path}")
