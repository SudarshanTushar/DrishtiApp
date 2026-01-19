# backend/intelligence/gis.py
import random

class GISEngine:
    """
    Serves Geospatial Layers (Polygons/Heatmaps) to the frontend.
    Simulates ISRO Bhuvan/Cartosat vector data.
    """

    @staticmethod
    def get_risk_layers(center_lat, center_lng):
        """
        Generates simulated 'Red Zones' around the area.
        In production, this would read Shapefiles/PostGIS.
        """
        layers = {
            "flood_zones": [],
            "landslide_clusters": []
        }

        # Simulate a FLOOD ZONE (Polygon) near a river
        # Creating a rough triangle/polygon around the location
        layers["flood_zones"].append({
            "id": "FLD_ZONE_01",
            "risk_level": "CRITICAL",
            "coordinates": [
                [center_lat + 0.02, center_lng - 0.02],
                [center_lat + 0.03, center_lng + 0.01],
                [center_lat + 0.01, center_lng + 0.03],
                [center_lat - 0.01, center_lng + 0.01]
            ],
            "info": "Brahmaputra Overflow (Level: 14m)"
        })

        # Simulate LANDSLIDE CLUSTERS (Circles)
        # Randomly place 3 unstable slope zones
        for i in range(3):
            offset_lat = random.uniform(-0.05, 0.05)
            offset_lng = random.uniform(-0.05, 0.05)
            layers["landslide_clusters"].append({
                "id": f"LSL_ZONE_{i}",
                "center": [center_lat + offset_lat, center_lng + offset_lng],
                "radius": random.randint(1000, 3000), # Meters
                "risk_level": "HIGH",
                "info": "Unstable Slope (Angle > 45°)"
            })

        return layers
