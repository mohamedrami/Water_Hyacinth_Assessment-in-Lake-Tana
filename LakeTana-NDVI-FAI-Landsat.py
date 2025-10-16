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

# 2. Authenticate & Initialize
ee.Authenticate()
ee.Initialize(project='Your-Project-ID')

# 3. Mount Google Drive and Load ROI
drive.mount('/content/drive')
gdf = gpd.read_file('/content/drive/MyDrive/shp/Area_of_study_Bigger.shp')
roi = geemap.geopandas_to_ee(gdf)

# 4. Function to compute both NDVI and FAI from Landsat
def compute_ndvi_fai(image):
    scale = 0.0000275
    offset = -0.2

    red = image.select('SR_B4').multiply(scale).add(offset)
    nir = image.select('SR_B5').multiply(scale).add(offset)
    swir = image.select('SR_B6').multiply(scale).add(offset)

    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

    # FAI
    red_wl, nir_wl, swir_wl = 655, 865, 1609
    slope = (swir.subtract(red)).multiply((nir_wl - red_wl) / (swir_wl - red_wl))
    baseline = red.add(slope)
    fai = nir.subtract(baseline).rename('FAI')

    return image.addBands([ndvi, fai])

# 5. Function to compute masked area using both NDVI + FAI
def get_ndvi_fai_monthly(year, month):
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-28' if month != 12 else f'{year}-{month:02d}-31'

    ls = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterDate(start_date, end_date)
        .filterBounds(roi)
        .filter(ee.Filter.lt('CLOUD_COVER', 20))
        .map(compute_ndvi_fai)
    )

    if ls.size().getInfo() == 0:
        print(f"⚠️ No images for {year}-{month:02d}")
        return None

    cloud = ls.aggregate_mean('CLOUD_COVER').getInfo()
    median = ls.median().clip(roi)

    ndvi = median.select('NDVI')
    fai = median.select('FAI')
    mask = ndvi.gt(0.3).And(fai.gt(0.002))

    area_img = mask.multiply(ee.Image.pixelArea())
    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi.geometry(),
        scale=30,
        maxPixels=1e10
    )

    area_sqkm = stats.get('NDVI').getInfo()
    if area_sqkm is None:
        return None

    return {
        'Year': year,
        'Month': month,
        'Date of Satellite Selected': start_date,
        'Cloud Cover Percentage': round(cloud, 2),
        'Area of Water Hyacinth in Lake Tana': round(area_sqkm / 1e6, 2)
    }

# 6. Loop and Print Results
results = []
for year in range(2013, 2025):
    for month in [10, 11, 12]:
        try:
            result = get_ndvi_fai_monthly(year, month)
            if result:
                print(f"✅ {year}-{month:02d}: {result['Area of Water Hyacinth in Lake Tana']} km² | Cloud: {result['Cloud Cover Percentage']}%")
                results.append(result)
        except Exception as e:
            print(f"❌ Error {year}-{month:02d}: {e}")

# 7. Export to Excel
df = pd.DataFrame(results)
df = df[[
    'Year',
    'Month',
    'Date of Satellite Selected',
    'Cloud Cover Percentage',
    'Area of Water Hyacinth in Lake Tana'
]]
df = df.sort_values(by='Date of Satellite Selected')

excel_path = 'NDVI_FAI_Combined_Landsat_2013_2024.xlsx'
df.to_excel(excel_path, index=False)

# 8. Download
from google.colab import files
print(f"\n📁 Final Excel file saved as: {excel_path}")
files.download(excel_path)
