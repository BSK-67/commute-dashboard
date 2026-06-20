import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from http.server import BaseHTTPRequestHandler
import json
from odsay import get_routes
from simulator import simulate_route, recommend_depart_time
import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            routes = get_routes()
            if isinstance(routes, dict) and "error" in routes:
                self.wfile.write(json.dumps({"error": routes["error"]}).encode())
                return

            results = []
            for i, route in enumerate(routes):
                sim = simulate_route(route)
                results.append({
                    "id": chr(65 + i),
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
            result = {
                "routes": results,
                "recommended": best["id"],
                "now": datetime.datetime.now().strftime("%H:%M")
            }
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())
