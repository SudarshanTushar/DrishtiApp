import time

class ResourceSentinel:
    """
    Manages critical resources (Water, Meds, Fuel, Shelter).
    Includes a 'Trust Score' for crowdsourced data.
    """
    
    # In-memory storage for the demo
    STORES = [
        {"id": "R1", "type": "WATER", "lat": 26.15, "lng": 91.74, "qty": "500L", "verified": True},
        {"id": "R2", "type": "MEDICAL", "lat": 26.13, "lng": 91.72, "qty": "Level 1 Kit", "verified": True}
    ]

    @staticmethod
    def add_resource(res_type, lat, lng, qty, is_admin=False):
        new_res = {
            "id": f"RES-{int(time.time())}",
            "type": res_type,
            "lat": lat,
            "lng": lng,
            "qty": qty,
            "verified": is_admin,
            "timestamp": time.time()
        }
        ResourceSentinel.STORES.append(new_res)
        return new_res

    @staticmethod
    def get_all():
        return ResourceSentinel.STORES
