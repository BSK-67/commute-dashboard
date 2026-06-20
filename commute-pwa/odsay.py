import requests
from urllib.parse import quote
from config import ODSAY_API_KEY, ORIGIN_LAT, ORIGIN_LNG, DEST_LAT, DEST_LNG

ODSAY_URL = "https://api.odsay.com/v1/api/searchPubTransPathT"

def get_routes():
    params = {
        "SX": ORIGIN_LNG,
        "SY": ORIGIN_LAT,
        "EX": DEST_LNG,
        "EY": DEST_LAT,
        "apiKey": ODSAY_API_KEY,
    }
    try:
        res = requests.get(ODSAY_URL, params=params, timeout=5)
        data = res.json()
        paths = data.get("result", {}).get("path", [])
        routes = []
        for path in paths[:3]:
            info = path.get("info", {})
            sub_paths = path.get("subPath", [])
            steps = []
            for sp in sub_paths:
                t = sp.get("trafficType")
                if t == 1:  # 지하철
                    steps.append({
                        "type": "subway",
                        "name": sp.get("lane", [{}])[0].get("name", "지하철"),
                        "start": sp.get("startName", ""),
                        "end": sp.get("endName", ""),
                        "time": sp.get("sectionTime", 0),
                        "stationID": sp.get("startID", "")
                    })
                elif t == 2:  # 버스
                    steps.append({
                        "type": "bus",
                        "name": sp.get("lane", [{}])[0].get("busNo", "버스"),
                        "start": sp.get("startName", ""),
                        "end": sp.get("endName", ""),
                        "time": sp.get("sectionTime", 0),
                        "stationID": sp.get("startID", ""),
                        "busID": sp.get("lane", [{}])[0].get("busID", "")
                    })
                elif t == 3:  # 도보
                    steps.append({
                        "type": "walk",
                        "time": sp.get("sectionTime", 0)
                    })
            routes.append({
                "totalTime": info.get("totalTime", 0),
                "transferCount": info.get("trafficCount", 0),
                "steps": steps
            })
        return routes
    except Exception as e:
        return {"error": str(e)}
