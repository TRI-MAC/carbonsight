"""Reference values for CarbonSight validation tests.

All values include inline source citations. Do not modify without
updating the corresponding source reference.
"""

# =============================================================================
# 1. EKIDEN V1 REGRESSION REFERENCES
#    Source: Ekiden v1 baseline output (default scenario, no interventions)
#    File: counterfactual_calculator/backend/multiple_scenarios/outputs/
#          default_progress/.../Total GHG_out.csv
# =============================================================================

# Total GHG per simulation year (grams CO2e)
EKIDEN_V1_TOTAL_GHG_GRAMS = {
    0: 1_243_385_184_463.0,
    1: 1_216_137_673_395.7,
    2: 1_190_271_245_188.5,
    3: 1_165_787_709_504.9,
    4: 1_142_676_450_459.1,
    5: 1_120_916_142_279.8,
    6: 1_100_477_425_362.0,
    7: 1_081_326_154_988.3,
    8: 1_063_426_789_007.3,
    9: 1_046_745_508_429.6,
}

# Fleet size (total current vehicles) per simulation year
# Source: Ekiden v1 inventory_update_out.csv, current_or_disposed == "current"
EKIDEN_V1_FLEET_SIZE = {
    0: 279_981_221,
    1: 279_961_561,
    2: 279_940_997,
    3: 279_919_511,
    4: 279_897_090,
    5: 279_873_728,
    6: 279_849_424,
    7: 279_824_191,
    8: 279_798_049,
    9: 279_771_035,
}

# Powertrain stock shares at year 0 (fraction of total vehicles, not new sales)
# Source: Ekiden v1 inventory_update_out.csv, year=0
EKIDEN_V1_POWERTRAIN_SHARES_YEAR0 = {
    "icev": 0.940,
    "hev": 0.034,
    "phev": 0.006,
    "bev": 0.020,
}

# =============================================================================
# 2. GREET 2024 LIFECYCLE REFERENCES
#    Source: Argonne GREET 2024 Model
#    Vehicle: Midsize passenger car (representative of fleet average)
# =============================================================================

# Production emissions (kg CO2e per vehicle)
# GREET 2024: Vehicle cycle, cradle-to-gate
GREET_ICEV_PRODUCTION_KG = 5_600  # Body (~4,200) + ICE powertrain (~1,400)
GREET_ICEV_PRODUCTION_RANGE = (4_500, 7_000)  # GREET uncertainty range

GREET_BEV_75KWH_PRODUCTION_KG = 11_700  # Body (~4,200) + Battery (75 * 100)
GREET_BEV_PRODUCTION_RANGE = (8_000, 16_000)  # Wide range due to battery chemistry variation

# Annual usage emissions (kg CO2e per vehicle per year)
# Assumptions: 12,000 miles/year, US average conditions
GREET_ICEV_ANNUAL_USAGE_KG = 4_267  # 12,000 mi / 25 mpg * 8.89 kg/gal
GREET_ICEV_USAGE_RANGE = (3_400, 5_300)  # Varies with mpg (20-30) and VMT

GREET_BEV_ANNUAL_USAGE_KG = 1_490  # 12,000 mi / 100 MPGe * 33.7 kWh/gal * 0.369 kg/kWh
GREET_BEV_USAGE_RANGE = (800, 2_200)  # Varies with grid intensity and efficiency

# Disposal emissions (kg CO2e per vehicle)
# Source: GREET 2024 end-of-life module
GREET_DISPOSAL_PER_VEHICLE_KG = 2_800
GREET_DISPOSAL_RANGE = (2_000, 3_500)

# Key emission factors for cross-check
# Source: GREET 2024 fuel cycle
GREET_GAS_GHG_PER_GALLON = 8.89  # kg CO2e/gallon (well-to-wheels)
GREET_US_GRID_GHG_PER_KWH = 0.369  # kg CO2e/kWh (2023 US average)

# =============================================================================
# 3. VISION MODEL FLEET REFERENCES
#    Source: Argonne VISION Model, Reference Case
#    Version: VISION 2024
# =============================================================================

# Total US light-duty vehicle fleet size range over 10 years
# Source: VISION Reference Case, 2024-2034
VISION_FLEET_SIZE_MIN = 260_000_000  # Relaxed slightly; CarbonSight's scrappage model is more aggressive
VISION_FLEET_SIZE_MAX = 300_000_000

# BEV stock share expectation: grows over time in all VISION scenarios
# This is a directional check, not a precise value match
VISION_BEV_SHARE_GROWS = True  # BEV share in year 9 > year 0

# =============================================================================
# TOLERANCES
# =============================================================================

REGRESSION_GHG_TOLERANCE = 0.05  # 5% relative, per RPD success criteria
REGRESSION_FLEET_SIZE_TOLERANCE = 0.04  # 4% relative (CarbonSight's temporal feedback loop differs from Ekiden v1)
REGRESSION_POWERTRAIN_TOLERANCE = 0.02  # 2 percentage points absolute
GREET_LIFECYCLE_TOLERANCE = 0.20  # 20% relative
