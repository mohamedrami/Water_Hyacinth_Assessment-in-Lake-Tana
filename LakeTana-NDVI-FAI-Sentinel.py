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

# 3. Mount Google Drive and Load ROI
drive.mount('/content/drive')
gdf = gpd.read_file('/content/drive/MyDrive/shp/Area_of_study_Bigger.shp')
roi = geemap.geopandas_to_ee(gdf)

# 4. Compute NDVI + FAI for Sentinel-2
def compute_ndvi_fai_sentinel(image):
    red = image.select('B4')
    nir = image.select('B8')
    swir = image.select('B11')

    # NDVI
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

    # FAI for Sentinel-2
    red_wl, nir_wl, swir_wl = 665, 842, 1610
    slope = (swir.subtract(red)).multiply((nir_wl - red_wl) / (swir_wl - red_wl))
    baseline = red.add(slope)
    fai = nir.subtract(baseline).rename('FAI')

    return image.addBands([ndvi, fai])

# 5. Analyze each month using NDVI + FAI integration
def get_ndvi_fai_monthly_s2(year, month):
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-28' if month != 12 else f'{year}-{month:02d}-31'

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(roi)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(compute_ndvi_fai_sentinel)
    )

    if s2.size().getInfo() == 0:
        print(f"⚠️ No images for {year}-{month:02d}")
        return None

    cloud = s2.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE').getInfo()
    median = s2.median().clip(roi)

    ndvi = median.select('NDVI')
    fai = median.select('FAI')
    mask = ndvi.gt(0.3).And(fai.gt(0.002))

    area_img = mask.multiply(ee.Image.pixelArea())
    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi.geometry(),
        scale=10,
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

# 6. Loop over years and months and print results
results = []
for year in range(2016, 2025):
    for month in [10, 11, 12]:
        try:
            result = get_ndvi_fai_monthly_s2(year, month)
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

excel_path = 'NDVI_FAI_Combined_Sentinel_2016_2024.xlsx'
df.to_excel(excel_path, index=False)

# 8. Download the Excel File
from google.colab import files
print(f"\n📁 Final Excel file saved as: {excel_path}")
files.download(excel_path)
