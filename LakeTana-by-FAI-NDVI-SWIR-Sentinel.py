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

# 3. Mount Google Drive and Load AOI Shapefile
drive.mount('/content/drive')
gdf = gpd.read_file('/content/drive/MyDrive/shp/Area_of_study_Bigger.shp')
roi = geemap.geopandas_to_ee(gdf)

# 4. Compute FAI + NDVI + SWIR for Sentinel-2
def compute_all_indices_sentinel(image):
    red  = image.select('B4')
    green = image.select('B3')
    nir  = image.select('B8')
    swir = image.select('B11')

    # NDVI = (NIR - RED) / (NIR + RED)
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

    # FAI = NIR - (RED + slope)
    red_wl, nir_wl, swir_wl = 665, 842, 1610
    slope = (swir.subtract(red)).multiply((nir_wl - red_wl) / (swir_wl - red_wl))
    baseline = red.add(slope)
    fai = nir.subtract(baseline).rename('FAI')

    return image.addBands([fai, ndvi, swir.rename('SWIR1')])

# 5. Monthly masked area function
def get_monthly_area_fai_ndvi_swir_s2(year, month):
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-28' if month != 12 else f'{year}-{month:02d}-31'

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(roi)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(compute_all_indices_sentinel)
    )

    if s2.size().getInfo() == 0:
        print(f"⚠️ No images for {year}-{month:02d}")
        return None

    cloud = s2.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE').getInfo()
    median = s2.median().clip(roi)

    fai   = median.select('FAI')
    ndvi  = median.select('NDVI')
    swir1 = median.select('SWIR1')

    mask = fai.gt(0.002).And(ndvi.gt(0.3)).And(swir1.lt(0.08))

    area_img = mask.multiply(ee.Image.pixelArea())
    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi.geometry(),
        scale=10,
        maxPixels=1e10
    )

    values = stats.values().getInfo()
    if not values or values[0] is None:
        return None

    area_km2 = values[0] / 1e6

    return {
        'Year': year,
        'Month': month,
        'Date of Satellite Selected': start_date,
        'Cloud Cover Percentage': round(cloud, 2),
        'Area of Water Hyacinth in Lake Tana': round(area_km2, 2)
    }

# 6. Run analysis 2016–2024 (Oct–Dec)
results = []
for year in range(2016, 2025):
    for month in [10, 11, 12]:
        try:
            result = get_monthly_area_fai_ndvi_swir_s2(year, month)
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

excel_path = 'FAI_NDVI_SWIR_Sentinel_2016_2024.xlsx'
df.to_excel(excel_path, index=False)

# 8. Download Excel
from google.colab import files
print(f"\n📁 Final Excel file saved as: {excel_path}")
files.download(excel_path)
