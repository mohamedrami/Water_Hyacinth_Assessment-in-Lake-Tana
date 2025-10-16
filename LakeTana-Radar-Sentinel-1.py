# Research Project: Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana
# Authours: Mohamed Rami Mahmoud , Luis A. Garcia , Ahmed Medhat  and Mostafa Aboelkhear  
# Developer: Prof. Mohamed Rami Mahmoud (ORCID: http://orcid.org/0000-0002-3393-987X)
# Contact: ORCID: http://orcid.org/0000-0002-3393-987X
# Version: <v1.0> | Date: <2025-10-16>

import ee
import geemap
import geopandas as gpd
import pandas as pd
import datetime
import calendar
from google.colab import drive, files

# Mount Google Drive
drive.mount('/content/drive')

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize(project='Your-Project-ID')

# Path to your shapefile
area_shp_path = '/content/drive/MyDrive/shp/Area_of_study_Bigger.shp'
area_gdf = gpd.read_file(area_shp_path)

def gdf_to_fc(gdf):
    import json
    geojson = json.loads(gdf.to_json())
    features = [ee.Feature(ee.Geometry(f['geometry'])) for f in geojson['features']]
    return ee.FeatureCollection(features)

area_fc = gdf_to_fc(area_gdf)
area_geom = area_fc.geometry()

sentinel1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filterBounds(area_geom)

years = list(range(2014, 2025))  # Now includes 2024
months = [10, 11, 12]  # October, November, December

results = []

for year in years:
    for month in months:
        first_day = datetime.date(year, month, 1)
        last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
        filtered = sentinel1.filterDate(first_day.isoformat(), last_day.isoformat())

        if filtered.size().getInfo() == 0:
            print(f"No images found for {year}-{month:02d}")
            continue

        # Get first image date in the month as the selected date
        first_image = filtered.first()
        date_selected = ee.Date(first_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()

        # Sentinel-1 does not have cloud cover; set to 0 or 'N/A'
        cloud_cover = 0

        median_img = filtered.median()
        vh_band = median_img.select('VH').unitScale(-25, 0)
        hyacinth_mask = vh_band.gt(0.2)
        area_img = hyacinth_mask.multiply(ee.Image.pixelArea())
        total_area = area_img.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=area_geom,
            scale=10,
            maxPixels=1e13
        ).get('VH')
        area_km2 = ee.Number(total_area).divide(1e6)

        results.append({
            'Year': year,
            'Month': month,
            'Date of Satellite Selected': date_selected,
            'Cloud Cover Percentage': cloud_cover,
            'Area of Water Hyacinth in Lake Tana': area_km2
        })

        print(f"{year}-{month:02d}: {area_km2.getInfo() if area_km2 else 0:.2f} km²")

df = pd.DataFrame(results)

def get_value(val):
    try:
        return val.getInfo() if hasattr(val, 'getInfo') else val
    except:
        return None

df['Area of Water Hyacinth in Lake Tana'] = df['Area of Water Hyacinth in Lake Tana'].apply(get_value)

# Reorder columns as requested
columns_order = [
    'Year',
    'Month',
    'Date of Satellite Selected',
    'Cloud Cover Percentage',
    'Area of Water Hyacinth in Lake Tana'
]
df = df[columns_order]

# Save to Excel in your Google Drive
excel_path = '/content/drive/MyDrive/Water_Hyacinth_Area_Tana_Sentinel1.xlsx'
df.to_excel(excel_path, index=False)
print(f"Results saved to: {excel_path}")

output_path = 'Radar_prex_area_results.xlsx'
df.to_excel(output_path, index=False)
files.download(output_path)
