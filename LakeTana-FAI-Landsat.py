# Research Project: Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana
# Authours: Mohamed Rami Mahmoud , Luis A. Garcia , Ahmed Medhat  and Mostafa Aboelkhear  
# Developer: Prof. Mohamed Rami Mahmoud (ORCID: http://orcid.org/0000-0002-3393-987X)
# Contact: ORCID: http://orcid.org/0000-0002-3393-987X
# Version: <v1.0> | Date: <2025-10-16>

# 1. Install and Import Libraries
!pip install geemap --quiet

import ee
import geemap
import pandas as pd
from datetime import datetime
import geopandas as gpd
from google.colab import drive

# 2. Authenticate & Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project='Your-Project-ID')


# 3. Mount Google Drive and Load ROI Shapefile
drive.mount('/content/drive')
gdf = gpd.read_file('/content/drive/MyDrive/shp/Area_of_study_Bigger.shp')
roi = geemap.geopandas_to_ee(gdf)

# 4. Function to compute FAI from Landsat scaled reflectance
def compute_fai_landsat(image):
    scale = 0.0000275
    offset = -0.2

    B4 = image.select('SR_B4').multiply(scale).add(offset)  # Red
    B5 = image.select('SR_B5').multiply(scale).add(offset)  # NIR
    B6 = image.select('SR_B6').multiply(scale).add(offset)  # SWIR1

    red_wl, nir_wl, swir_wl = 655, 865, 1609
    slope = (B6.subtract(B4)).multiply((nir_wl - red_wl) / (swir_wl - red_wl))
    baseline = B4.add(slope)
    fai = B5.subtract(baseline).rename('FAI')
    return image.addBands(fai)

# 5. Monthly analysis function
def get_fai_monthly_landsat(year, month):
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-28' if month != 12 else f'{year}-{month:02d}-31'

    # Merge Landsat 8 and 9 collections
    ls = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterDate(start_date, end_date)
        .filterBounds(roi)
        .filter(ee.Filter.lt('CLOUD_COVER', 20))
        .map(compute_fai_landsat)
    )

    if ls.size().getInfo() == 0:
        print(f"⚠️ No images for {year}-{month:02d}")
        return None

    cloud = ls.aggregate_mean('CLOUD_COVER').getInfo()
    median = ls.median().clip(roi)
    fai_mask = median.select('FAI').gt(0.005)
    area_img = fai_mask.multiply(ee.Image.pixelArea())

    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi.geometry(),
        scale=30,
        maxPixels=1e10
    )

    fai_area_sqkm = stats.get('FAI').getInfo()
    if fai_area_sqkm is None:
        return None

    return {
        'Year': year,
        'Month': month,
        'Date of Satellite Selected': start_date,
        'Cloud Cover Percentage': round(cloud, 2),
        'Area of Water Hyacinth in Lake Tana': round(fai_area_sqkm / 1e6, 2)
    }

# 6. Loop from 2013 to 2024 and print results
results = []
for year in range(2013, 2025):
    for month in [10, 11, 12]:
        try:
            result = get_fai_monthly_landsat(year, month)
            if result:
                print(f"✅ {year}-{month:02d}: {result['Area of Water Hyacinth in Lake Tana']} km² | Cloud: {result['Cloud Cover Percentage']}%")
                results.append(result)
        except Exception as e:
            print(f"❌ Error {year}-{month:02d}: {e}")

# 7. Export results to Excel
df = pd.DataFrame(results)
df = df[[
    'Year',
    'Month',
    'Date of Satellite Selected',
    'Cloud Cover Percentage',
    'Area of Water Hyacinth in Lake Tana'
]]
df = df.sort_values(by='Date of Satellite Selected')

excel_path = 'FAI_Landsat_2013_2024.xlsx'
df.to_excel(excel_path, index=False)

# 8. Download Excel
from google.colab import files
print(f"\n📁 Final Excel file saved as: {excel_path}")
files.download(excel_path)
