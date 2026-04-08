"""
Constants used throughout the application
"""

# Directory paths
DEFAULT_FIM_DIR = "C:\\DCR4402\\FIM"
DEFAULT_IFX_DIR = "C:\\DCR4402\\IFX"
DEFAULT_PRG_DIR = "C:\\DCR4402\\PRG"
DEFAULT_CPT_DIR = "C:\\DCR4402\\CPT"
DEFAULT_DBL_DIR = "C:\\DCR4402\\DBL"

# Application constants
APP_NAME = "Data Ferns 2026"
APP_VERSION = "1.0.0"
APP_TITLE = "Data Ferns 2026 - Traffic Analysis"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

# Message titles
MSG_TITLE_NORMAL = "Message - Data Ferns 2026"
MSG_TITLE_ERROR = "Error - Data Ferns 2026"
MSG_TITLE_WARNING = "Warning - Data Ferns 2026"
MSG_TITLE_SUCCESS = "Success - Data Ferns 2026"

# File formats
SUPPORTED_INPUT_FORMATS = ["FIM", "DBL"]
SUPPORTED_OUTPUT_FORMAT = "IFX"

# Sequence types
SEQUENCE_15 = 15
SEQUENCE_30 = 30
SEQUENCE_60 = 60
SEQUENCE_1440 = 1440

SEQUENCES = [SEQUENCE_15, SEQUENCE_30, SEQUENCE_60, SEQUENCE_1440]

# Vehicle types
VEHICLE_TYPE_TV = "TV"  # All vehicles
VEHICLE_TYPE_PL = "PL"  # Heavy vehicles
VEHICLE_TYPE_TVPL = "TVPL"  # TV and PL

# Mode types
MODE_TV_CONF = "1 - TV Conf."
MODE_PL_CONF = "11 - PL Conf."
MODE_TV_DISC = "1 - TV Disc."
MODE_TVPL_DISC = "TVPL"
MODE_TV_VIT = "TV Vit."
MODE_TVPL_VIT = "TVPL Vit."

# Road types
ROAD_TYPES = [
    "Route Nationale",
    "Route Départementale",
    "Autoroute",
    "Voie Rapide",
    "Rocade",
    "Voie Communale"
]

# Number of lanes
LANE_OPTIONS = [
    "2 Voies : 1x1",
    "3 Voies : 2x1",
    "4 Voies : 2x2",
    "6 Voies : 3x3",
    "Voie Unique"
]

# Direction types
DIRECTION_TYPES = [
    "Confondus",
    "Discriminés",
    "Sens 1",
    "Sens 2",
    "Sens 3"
]

# FIM File Structure
# File contains sequential row blocks, one per sensor/direction
# Each row has 12 values representing vehicle counts by speed class
# Speed bins are defined by their UPPER BOUNDS in the file header (e.g., [30, 40, 50, ...])
# These represent ranges: <20, 20-30, 30-40, 40-50, 50-60, 60-70, 70-80, 80-90, 90-100, 100-110, 110-120, 120-130, 130-150
# For mean speed calculation, use the CENTER of each range:
# Bin centers: [10, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140] km/h

# Vehicle class mapping in FIM data - SENSOR-LEVEL, not column-level
# Each sensor represents a COMPLETE vehicle class (all 12 columns combined)
# For 4-sensor files:
#   Sensor 0 (all 12 cols) = VL for Direction 1 (Sens 1)
#   Sensor 1 (all 12 cols) = PL for Direction 1 (Sens 1)
#   Sensor 2 (all 12 cols) = VL for Direction 2 (Sens 2)
#   Sensor 3 (all 12 cols) = PL for Direction 2 (Sens 2)
# For 2-sensor files:
#   Sensor 0 (all 12 cols) = All vehicles for Direction 1 (Sens 1)
#   Sensor 1 (all 12 cols) = All vehicles for Direction 2 (Sens 2)
FIM_SENSOR_VEHICLE_MAP = {
    4: {  # 4-sensor configuration
        0: {'direction': 'Sens 1', 'class': 'VL'},
        1: {'direction': 'Sens 1', 'class': 'PL'},
        2: {'direction': 'Sens 2', 'class': 'VL'},
        3: {'direction': 'Sens 2', 'class': 'PL'},
    },
    2: {  # 2-sensor configuration
        0: {'direction': 'Sens 1', 'class': 'ALL'},
        1: {'direction': 'Sens 2', 'class': 'ALL'},
    }
}

# Status messages
STATUS_OPENING = "Opening in progress... Please wait. Thank you"
STATUS_PROCESSING = "Processing in progress... Please wait. Thank you"
STATUS_SAVING = "Saving in progress..."
STATUS_COMPLETE = "Operation completed successfully"

# Excel sheet names
SHEET_BRUT = "BRUT"
SHEET_BEST = "BEST"
SHEET_INFO = "Informations"
SHEET_MENU = "MENU"
