"""
This module defines constants for allowed MIME types used in the application.
These constants are used to validate uploaded files and distinguish between
image files and geo files (e.g., KML/GeoJSON).
"""

# Allowed MIME types for uploaded files
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "application/geo+json",
    "application/vnd.google-earth.kml+xml",
    "application/json",
    "application/octet-stream"
}

# MIME types that are treated as geo files (KML/GeoJSON)
GEO_MIME_TYPES = {
    "application/vnd.google-earth.kml+xml",
    "application/octet-stream",
    "application/json",
    "application/geo+json"
}