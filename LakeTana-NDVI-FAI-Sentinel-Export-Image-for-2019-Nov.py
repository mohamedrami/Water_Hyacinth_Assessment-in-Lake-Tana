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

# ... (previous code sections for authentication, ROI loading, NDVI/FAI computation remain unchanged)

# 4. Compute NDVI + FAI for Sentinel-2 (existing function remains the same)
def compute_ndvi_fai_sentinel(image):
    red = image.select('B4')
    nir = image.select('B8')
    swir = image.select('B11')
    # NDVI calculation
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    # FAI calculation (Floating Algal Index for Sentinel-2)
    red_wl, nir_wl, swir_wl = 665, 842, 1610  # wavelengths for B4, B8, B11 in nm
    slope = (swir.subtract(red)).multiply((nir_wl - red_wl) / (swir_wl - red_wl))
    baseline = red.add(slope)
    fai = nir.subtract(baseline).rename('FAI')
    return image.addBands([ndvi, fai])

# 5. Function to get NDVI+FAI median for a given month (existing logic)
def get_ndvi_fai_monthly_s2(year, month):
    start_date = f'{year}-{month:02d}-01'
    end_date   = f'{year}-{month:02d}-28' if month != 12 else f'{year}-{month:02d}-31'
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterDate(start_date, end_date)
          .filterBounds(roi)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
          .map(compute_ndvi_fai_sentinel))
    if s2.size().getInfo() == 0:
        print(f"⚠️ No images for {year}-{month:02d}")
        return None
    cloud = s2.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE').getInfo()
    median = s2.median().clip(roi)  # median composite for the month, clipped to ROI
    ndvi = median.select('NDVI')
    fai  = median.select('FAI')
    mask = ndvi.gt(0.3).And(fai.gt(0.002))  # infected-area mask where NDVI>0.3 and FAI>0.002:contentReference[oaicite:5]{index=5}
    # (Note: This function originally returns stats; we will export images separately below)
    area_img = mask.multiply(ee.Image.pixelArea())
    stats = area_img.reduceRegion(**{
        'reducer': ee.Reducer.sum(),
        'geometry': roi.geometry(),
        'scale': 10,
        'maxPixels': 1e10
    })
    area_sq_m = stats.get('NDVI').getInfo()
    if area_sq_m is None:
        return None
    return {
        'Year': year,
        'Month': month,
        'Date of Satellite Selected': start_date,
        'Cloud Cover Percentage': round(cloud, 2),
        'Area of Water Hyacinth in Lake Tana (km^2)': round(area_sq_m / 1e6, 2)
    }

# 6. Loop over desired years and months to print results (existing)
results = []
for year in range(2019, 2020):
    for month in [11]:  # example: November 2019
        result = get_ndvi_fai_monthly_s2(year, month)
        if result:
            print(f"✅ {year}-{month:02d}: {result['Area of Water Hyacinth in Lake Tana (km^2)']} km²",
                  f"| Cloud: {result['Cloud Cover Percentage']}%")
            results.append(result)

# 7. Export tabular results to Excel (existing code)
# ... (DataFrame creation and to_excel, as in original script)

# 8. (Optional) Download the Excel file (existing code)
# ... (files.download call as in original script)

# 9. Export mask and index rasters to Google Drive (New additions)
export_year  = 2019  # Year to export (adjust as needed)
export_month = 11    # Month to export (adjust as needed)

# Recompute the monthly median image for the specified export date
export_start = f'{export_year}-{export_month:02d}-01'
export_end   = f'{export_year}-{export_month:02d}-28' if export_month != 12 else f'{export_year}-{export_month:02d}-31'
s2_export = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterDate(export_start, export_end)
             .filterBounds(roi)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
             .map(compute_ndvi_fai_sentinel))
median_img = s2_export.median().clip(roi)
ndvi_img   = median_img.select('NDVI')
fai_img    = median_img.select('FAI')
mask_img   = ndvi_img.gt(0.3).And(fai_img.gt(0.002))  # 0/1 mask of infected areas:contentReference[oaicite:6]{index=6}

# Prepare images for export
hyacinth_mask = mask_img.rename('WaterHyacinthMask').uint8()  # binary mask (0 = non-infected, 1 = infected)
ndvi_fai_img  = ndvi_img.addBands(fai_img)  # two-band image (NDVI and FAI raw values)

# Define export region and parameters
export_region = roi.geometry()  # Lake Tana ROI geometry for clipping
export_folder = 'LakeTana_Exports'  # Google Drive folder name (change as needed)

# Export 1: Binary mask GeoTIFF
task_mask = ee.batch.Export.image.toDrive(**{
    'image': hyacinth_mask,
    'description': f'LakeTana_HyacinthMask_{export_year}_{export_month:02d}',
    'folder': export_folder,
    'fileNamePrefix': f'LakeTana_HyacinthMask_{export_year}_{export_month:02d}',
    'region': export_region,
    'crs': 'EPSG:32637',   # WGS 84 / UTM Zone 37N:contentReference[oaicite:7]{index=7}
    'scale': 10,           # 10-meter spatial resolution:contentReference[oaicite:8]{index=8}
    'maxPixels': 1e10      # allow large exports (adjust if needed)
})
task_mask.start()

# Export 2: NDVI and FAI raw values GeoTIFF (2-band image)
task_indices = ee.batch.Export.image.toDrive(**{
    'image': ndvi_fai_img,
    'description': f'LakeTana_NDVI_FAI_{export_year}_{export_month:02d}',
    'folder': export_folder,
    'fileNamePrefix': f'LakeTana_NDVI_FAI_{export_year}_{export_month:02d}',
    'region': export_region,
    'crs': 'EPSG:32637',
    'scale': 10,
    'maxPixels': 1e10
})
task_indices.start()

print(f"🚀 Export tasks started for {export_year}-{export_month:02d}. "
      f"Check the Earth Engine Tasks console or your Drive folder '{export_folder}' for results.")
