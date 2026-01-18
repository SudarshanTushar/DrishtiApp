import heapq
import joblib
import pandas as pd

# Load AI Models (Mocking the load if files don't exist yet)
try:
    landslide_model = joblib.load('landslide_rf.pkl')
except:
    landslide_model = None

class RiskGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = {} # Adjacency list: start -> [(end, distance, static_features)]

    def add_edge(self, u, v, dist, slope, rock_hard, soil_moisture):
        self.nodes.add(u)
        self.nodes.add(v)
        if u not in self.edges: self.edges[u] = []
        if v not in self.edges: self.edges[v] = []
        
        # Store edge attributes for AI inference later
        attrs = {'dist': dist, 'slope': slope, 'rock_hard': rock_hard, 'soil': soil_moisture}
        self.edges[u].append((v, attrs))
        self.edges[v].append((u, attrs))

    def calculate_dynamic_weight(self, attrs, current_rain):
        """
        The Magic Formula:
        Weight = Distance * (1 + Landslide_Probability + Flood_Risk)
        """
        dist = attrs['dist']
        
        # 1. AI Inference (Landslide)
        risk_score = 0
        if landslide_model:
            # Create a single-row dataframe for prediction
            input_data = pd.DataFrame([{
                'slope': attrs['slope'],
                'rainfall_24h': current_rain,
                'soil_moisture': attrs['soil'],
                'rock_type_hard': attrs['rock_hard'],
                'vegetation_index': 0.5 # Default
            }])
            risk_score = landslide_model.predict(input_data)[0]
        else:
            # Fallback heuristic if ML model missing
            risk_score = (attrs['slope'] / 90) * (current_rain / 200)

        # 2. Risk Penalty
        # If Risk > 0.8, the cost skyrockets (effectively blocking the road)
        penalty_factor = 1 + (risk_score * 10) 
        
        return dist * penalty_factor, risk_score

    def find_safest_path(self, start, end, current_rain):
        # Priority Queue: (Cumulative_Cost, Current_Node, Path_List, Explanations)
        pq = [(0, start, [], [])]
        visited = set()
        min_costs = {node: float('inf') for node in self.nodes}
        min_costs[start] = 0

        while pq:
            cost, u, path, explanation = heapq.heappop(pq)

            if u in visited: continue
            visited.add(u)
            
            path = path + [u]

            if u == end:
                return path, cost, explanation

            if u in self.edges:
                for v, attrs in self.edges[u]:
                    if v in visited: continue
                    
                    # Calculate Edge Weight using AI
                    edge_weight, risk_score = self.calculate_dynamic_weight(attrs, current_rain)
                    new_cost = cost + edge_weight

                    if new_cost < min_costs[v]:
                        min_costs[v] = new_cost
                        
                        # Add explanation for this segment
                        seg_info = {
                            'from': u, 'to': v, 
                            'risk': round(risk_score, 2),
                            'rain': current_rain
                        }
                        heapq.heappush(pq, (new_cost, v, path, explanation + [seg_info]))

        return None, float('inf'), []

# --- TEST HARNESS ---
if __name__ == "__main__":
    g = RiskGraph()
    # Adding Edges: (u, v, dist_km, slope, rock_hard, soil_moisture)
    g.add_edge("Guwahati", "Shillong", 100, 45, 0, 60) # High Slope, Soft Rock
    g.add_edge("Guwahati", "Tezpur", 180, 10, 1, 30)   # Low Slope, Hard Rock
    g.add_edge("Tezpur", "Shillong", 150, 20, 1, 40)   # Medium

    print("🚑 Calculating Safe Route (Rain = 20mm)...")
    path, cost, _ = g.find_safest_path("Guwahati", "Shillong", 20)
    print(f"   Route: {path} (Cost: {cost:.2f})")

    print("\n🚑 Calculating Safe Route (Rain = 250mm - STORM)...")
    path, cost, expl = g.find_safest_path("Guwahati", "Shillong", 250)
    print(f"   Route: {path} (Cost: {cost:.2f})")
    print("   ⚠️ Why? See Risk Scores:", [x['risk'] for x in expl])