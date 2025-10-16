# Research Project: Environmental Coherence Framework for Multi-Sensor Remote Sensing: Water Hyacinth Assessment in Lake Tana
# Authours: Mohamed Rami Mahmoud , Luis A. Garcia , Ahmed Medhat  and Mostafa Aboelkhear  
# Developer: Prof. Mohamed Rami Mahmoud (ORCID: http://orcid.org/0000-0002-3393-987X)
# Contact: ORCID: http://orcid.org/0000-0002-3393-987X
# Version: <v1.0> | Date: <2025-10-16>

#  Hybrid Water Hyacinth Detection using Sentinel-2 + Sentinel-1 (GEE + Colab)
!pip install -q earthengine-api geemap geopandas

import ee
import geemap
import geopandas as gpd
import pandas as pd
import datetime
import calendar
from google.colab import drive, files

# Mount and Authenticate
drive.mount('/content/drive')
ee.Authenticate()
ee.Initialize(project='Your-Project-ID')

# Load shapefile as FeatureCollection
shp_path = '/content/drive/MyDrive/shp/Area_of_study_Bigger.shp'
gdf = gpd.read_file(shp_path)

def gdf_to_fc(gdf):
    import json
    geojson = json.loads(gdf.to_json())
    features = [ee.Feature(ee.Geometry(f['geometry'])) for f in geojson['features']]
    return ee.FeatureCollection(features)

roi = gdf_to_fc(gdf).geometry()

years = list(range(2016, 2025))
months = [10, 11, 12]
results = []

def get_sentinel2_mask(start, end):
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(start, end) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 70)) \
        .map(lambda img: img.clip(roi))

    img = s2.sort('CLOUDY_PIXEL_PERCENTAGE').first()

    # ✅ Safely check if the image is valid
    try:
        _ = img.bandNames().size().getInfo()
    except Exception:
        return None, None, None

    def add_indices(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        fai = image.expression(
            'B08 - (B04 + (B11 - B04) * (0.865 - 0.665)/(1.61 - 0.665))',
            {
                'B04': image.select('B4'),
                'B08': image.select('B8'),
                'B11': image.select('B11')
            }).rename('FAI')
        swir = image.select('B11').divide(10000).rename('SWIR')
        return image.addBands([ndvi, fai, swir])

    img = add_indices(img)
    ndvi = img.select('NDVI')
    fai = img.select('FAI')
    swir = img.select('SWIR')

    mask = ndvi.gt(0.3).And(fai.gt(0.01)).And(swir.lt(0.1))
    cloud_cover = img.get('CLOUDY_PIXEL_PERCENTAGE')
    date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')

    return mask, cloud_cover, date

def get_sentinel1_mask(start, end):
    s1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
        .filterBounds(roi) \
        .filterDate(start, end) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW'))

    if s1.size().getInfo() == 0:
        return None

    img = s1.mosaic()
    vv = img.select('VV')
    vh = img.select('VH')
    ratio = vv.divide(vh).rename('VVVH_ratio')
    radar_mask = vh.lt(0.1).And(ratio.gt(1.3))
    return radar_mask

for year in years:
    for month in months:
        start = datetime.date(year, month, 1).isoformat()
        end = datetime.date(year, month, calendar.monthrange(year, month)[1]).isoformat()

        print(f"\n🔄 Processing {year}-{month:02d}...")

        # Get masks
        optical_mask, cloud_cover, s2_date = get_sentinel2_mask(start, end)
        cloud_pct = cloud_cover.getInfo() if cloud_cover else None
        radar_mask = get_sentinel1_mask(start, end)

        # Fusion logic
        if optical_mask and cloud_pct is not None and cloud_pct < 30:
            final_mask = optical_mask if not radar_mask else optical_mask.Or(radar_mask)
            source = 'Hybrid (Optical+Radar)'
        elif radar_mask:
            final_mask = radar_mask
            source = 'Radar only'
        elif optical_mask:
            final_mask = optical_mask
            source = 'Optical only'
        else:
            print(f"⚠️ No valid data for {year}-{month:02d}")
            continue

        # Area calculation
        area_image = final_mask.multiply(ee.Image.pixelArea()).rename('area')
        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=10,
            maxPixels=1e13
        )

        try:
            area_km2 = ee.Number(stats.get('area')).divide(1e6).getInfo()
        except Exception:
            print(f"⚠️ Unable to compute area for {year}-{month:02d}")
            continue

        results.append({
            'Year': year,
            'Month': month,
            'Date of Satellite Selected': s2_date.getInfo() if s2_date else 'Radar only',
            'Cloud Cover Percentage': round(cloud_pct, 2) if cloud_pct else 'N/A',
            'Area of Water Hyacinth in Lake Tana': round(area_km2, 2),
            'Source Used': source
        })

        print(f"✅ {year}-{month:02d}: {area_km2:.2f} km² ({source})")

# Create and save DataFrame
df = pd.DataFrame(results)
df = df[[
    'Year',
    'Month',
    'Date of Satellite Selected',
    'Cloud Cover Percentage',
    'Area of Water Hyacinth in Lake Tana',
    'Source Used'
]]

save_path = '/content/drive/MyDrive/Water_Hyacinth_HybridFusion_Final.xlsx'
df.to_excel(save_path, index=False)
print(f"\n📁 Excel saved to: {save_path}")

local_copy = 'Water_Hyacinth_HybridFusion_Final.xlsx'
df.to_excel(local_copy, index=False)
files.download(local_copy)
