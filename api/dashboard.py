from http.server import BaseHTTPRequestHandler
import json, sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from odsay import get_routes
from simulator import simulate_route, recommend_depart_time

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        try:
            routes = get_routes()
            results = []
            for i, route in enumerate(routes):
                sim = simulate_route(route)
                results.append({
                    "id": chr(65+i),
                    "totalTime": route["totalTime"],
                    "transferCount": route["transferCount"],
                    "steps": route["steps"],
                    "timeline": sim["timeline"],
                    "arriveTime": sim["arriveTime"],
                    "marginMin": sim["marginMin"],
                    "onTime": sim["onTime"],
                    "recommendDepart": recommend_depart_time(route["totalTime"]),
                })
            best = min(results, key=lambda r: abs(r["marginMin"]) if r["onTime"] else 9999)
            self.wfile.write(json.dumps({
                "routes": results,
                "recommended": best["id"],
                "now": datetime.datetime.now().strftime("%H:%M")
            }).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())
