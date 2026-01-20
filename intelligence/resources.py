import time

class ResourceSentinel:
    """
    Manages critical resources (Water, Meds, Fuel, Shelter).
    """
    
    # In-memory storage for the demo
    STORES = [
        {"id": "R1", "type": "WATER", "lat": 26.15, "lng": 91.74, "qty": "500L", "verified": True, "timestamp": time.time()},
        {"id": "R2", "type": "MEDICAL", "lat": 26.13, "lng": 91.72, "qty": "Level 1 Kit", "verified": True, "timestamp": time.time()}
    ]

    @staticmethod
    def add_resource(res_type, lat, lng, qty, is_admin=False):
        new_res = {
            "id": f"RES-{int(time.time()*1000)}", # Unique ID
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
        # Sort by newest first
        return sorted(ResourceSentinel.STORES, key=lambda x: x['timestamp'], reverse=True)

    @staticmethod
    def verify_resource(res_id):
        for res in ResourceSentinel.STORES:
            if res["id"] == res_id:
                res["verified"] = True
                return True
        return False

    @staticmethod
    def delete_resource(res_id):
        # Filter out the resource with the matching ID
        initial_len = len(ResourceSentinel.STORES)
        ResourceSentinel.STORES = [r for r in ResourceSentinel.STORES if r["id"] != res_id]
        return len(ResourceSentinel.STORES) < initial_len
