"""Central application and data-format version metadata.

PRODUCT_VERSION is the in-app product line shown to users. RELEASE_VERSION is
kept separately because the first distributable release is tagged v1.0.0.
MACRO_SCHEMA_VERSION describes saved macro data and must not follow the app
version: it changes only when the serialized macro contract changes.
"""

PRODUCT_NAME = "Apex Auto-Clicker"
PUBLISHER_NAME = "Kastrick"
PRODUCT_VERSION = "1.1"
RELEASE_VERSION = "1.0.0"
RELEASE_TAG = f"v{RELEASE_VERSION}"
MACRO_SCHEMA_VERSION = "11.0"
EXECUTABLE_BASENAME = "apex-autoclicker"
EXECUTABLE_NAME_WINDOWS = f"{EXECUTABLE_BASENAME}.exe"
