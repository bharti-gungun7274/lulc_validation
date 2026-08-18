# ============================================================
# LULC VALIDATION CONFIGURATION
# ============================================================

YEARS = [2018, 2020, 2022, 2024]

NODATA_VALUE = 255

LULC_CLASSES = {
    0: "Water",
    1: "Trees",
    2: "Grass",
    3: "Flooded vegetation",
    4: "Crops",
    5: "Shrub and scrub",
    6: "Built-up",
    7: "Bare",
    8: "Snow and ice"
}

CRS = "EPSG:32643"

RESOLUTION = 10

VALIDATION_POINTS_PER_YEAR = 240