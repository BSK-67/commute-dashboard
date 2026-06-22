"""
출근 경로 안내 백엔드 — PWA + Railway 배포 완성본
프론트엔드 정적 파일도 Flask에서 함께 서빙
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os

# 프론트엔드 폴더 경로
FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND, static_url_path="")
CORS(app)

# ── API 키 ───────────────────────────────────────────────────
ODSAY_API_KEY    = os.getenv("ODSAY_API_KEY",    "mTXJ4RrO4uXr6CAYlN+S3A")
SEOUL_SUBWAY_KEY = os.getenv("SEOUL_SUBWAY_KEY",  "456b774a51716b7337346c66616369")
BUS_API_KEY      = os.getenv("BUS_API_KEY",       "8b6717046b2e5e668ab6f70aa22bbd2e5a0e7144e19b350420a5aed88349b545")

LINE_COLORS = {
    "1": "#0052A4", "2": "#00A84D", "3": "#EF7C1C",
    "4": "#00A5DE", "5": "#996CAC", "6": "#CD7C2F",
    "7": "#747F00", "8": "#E6186C", "9": "#BDB092",
}

# ── 정적 파일 서빙 (PWA) ────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND, "index.html")

@app.route("/sw.js")
def sw():
    return send_from_directory(FRONTEND, "sw.js",
                               mimetype="application/javascript")

@app.route("/manifest.json")
def manifest():
    return send_from_directory(FRONTEND, "manifest.json",
                               mimetype="application/manifest+json")

@app.route("/icons/<path:filename>")
def icons(filename):
    return send_from_directory(os.path.join(FRONTEND, "icons"), filename)

# ── ODsay: 역명 → 좌표 ─────────────────────────────────────
def search_station(keyword: str) -> dict | None:
    url = "https://api.odsay.com/v1/api/searchStation"
    import urllib.parse
    encoded_key = urllib.parse.quote(ODSAY_API_KEY, safe="")
    full_url = f"{url}?apiKey={encoded_key}&stationName={urllib.parse.quote(keyword)}&stationClass=2&lang=0"
    try:
        data = requests.get(full_url, timeout=5).json()
        print(f"[search_station] response: {data}")
        s = data["result"]["station"][0]
        return {"x": s["x"], "y": s["y"], "name": s["stationName"]}
    except Exception as e:
        print(f"[search_station] {e}")
        return None

# ── ODsay: 경로 탐색 ────────────────────────────────────────
def get_odsay_route(sx, sy, ex, ey) -> dict | None:
    url = "https://api.odsay.com/v1/api/searchPubTransPathT"
    import urllib.parse
    encoded_key = urllib.parse.quote(ODSAY_API_KEY, safe="")
    full_url = f"{url}?apiKey={encoded_key}&SX={sx}&SY={sy}&EX={ex}&EY={ey}&SearchType=0&lang=0"
    try:
        data = requests.get(full_url, timeout=10).json()
        print(f"[get_odsay_route] response: {data}")
    except Exception as e:
        print(f"[get_odsay_route] {e}")
        return None

# ── 서울 지하철 실시간 ──────────────────────────────────────
def get_subway_realtime(station_name: str) -> list[dict]:
    url = (
        f"http://swopenapi.seoul.go.kr/api/subway/{SEOUL_SUBWAY_KEY}"
        f"/json/realtimeStationArrival/0/5/{requests.utils.quote(station_name)}"
    )
    try:
        data = requests.get(url, timeout=5).json()
        return [{
            "arrivalMsg":  item.get("arvlMsg2", ""),
            "remainSec":   int(item.get("barvlDt", 0)),
            "destination": item.get("bstatnNm", ""),
            "direction":   item.get("trainLineNm", ""),
        } for item in data.get("realtimeArrivalList", [])]
    except Exception as e:
        print(f"[get_subway_realtime] {e}")
        return []

# ── 버스 실시간 ─────────────────────────────────────────────
def get_bus_realtime(station_id: str) -> list[dict]:
    url = "http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid"
    params = {"serviceKey": BUS_API_KEY, "arsId": station_id, "resultType": "json"}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        return [{
            "busNo":      item.get("busRouteAbrv", ""),
            "arrivalMsg": item.get("arrmsg1", ""),
            "nextMsg":    item.get("arrmsg2", ""),
            "direction":  item.get("adirection", ""),
        } for item in data["msgBody"]["itemList"]]
    except Exception as e:
        print(f"[get_bus_realtime] {e}")
        return []

# ── 타임라인 변환 ───────────────────────────────────────────
def build_timeline(path: dict, arrive_time_str: str, buffer_min: int = 10) -> dict:
    info      = path["info"]
    sub_paths = path["subPath"]
    total_min = info["totalTime"]

    arrive_dt  = datetime.strptime(arrive_time_str, "%H:%M")
    depart_dt  = arrive_dt - timedelta(minutes=total_min + buffer_min)
    current_dt = depart_dt
    steps      = []

    for sp in sub_paths:
        t        = sp["trafficType"]
        duration = sp.get("sectionTime", 0)

        if t == 4:
            if not duration:
                continue
            steps.append({
                "type": "walk", "time": current_dt.strftime("%H:%M"),
                "label": "도보 이동",
                "detail": f"{sp.get('startName','출발')} → {sp.get('endName','도착')}",
                "duration": duration, "badge": f"도보 {duration}분",
            })
        elif t == 1:
            lane = sp["lane"][0]
            line_name = lane.get("name", "지하철")
            steps.append({
                "type": "subway", "time": current_dt.strftime("%H:%M"),
                "label": f"{line_name} 탑승",
                "detail": f"{sp.get('startName','')} → {sp.get('endName','')} ({sp.get('stationCount',0)}정거장)",
                "duration": duration, "badge": line_name,
                "color": LINE_COLORS.get(str(lane.get("subwayCode", "")), "#888"),
                "realtime_station": sp.get("startName", ""),
            })
        elif t in (2, 3):
            bus_no = sp["lane"][0].get("busNo", "버스")
            steps.append({
                "type": "bus", "time": current_dt.strftime("%H:%M"),
                "label": f"{bus_no}번 버스 탑승",
                "detail": f"{sp.get('startName','')} → {sp.get('endName','')} ({sp.get('stationCount',0)}정거장)",
                "duration": duration, "badge": f"{bus_no}번",
                "station_id": str(sp.get("startID", "")),
            })

        current_dt += timedelta(minutes=duration)

    steps.append({"type": "arrive", "time": arrive_dt.strftime("%H:%M"),
                  "label": "도착", "detail": "목적지 도착"})

    return {
        "departTime":    depart_dt.strftime("%H:%M"),
        "arriveTime":    arrive_dt.strftime("%H:%M"),
        "totalMin":      total_min + buffer_min,
        "routeMin":      total_min,
        "bufferMin":     buffer_min,
        "transferCount": info["transitCount"],
        "walkMin":       info.get("totalWalk", 0) // 60,
        "cost":          info.get("payment", 0),
        "steps":         steps,
    }

# ── API 엔드포인트 ───────────────────────────────────────────
@app.route("/api/route", methods=["POST"])
def route():
    body       = request.get_json()
    from_name  = body.get("from", "")
    to_name    = body.get("to", "")
    arrive_str = body.get("arriveTime", "09:00")
    buffer     = int(body.get("buffer", 10))

    origin = search_station(from_name)
    dest   = search_station(to_name)
    if not origin or not dest:
        return jsonify({"error": "출발지 또는 도착지를 찾을 수 없습니다."}), 400

    path = get_odsay_route(origin["x"], origin["y"], dest["x"], dest["y"])
    if not path:
        return jsonify({"error": "경로를 찾을 수 없습니다."}), 404

    result = build_timeline(path, arrive_str, buffer)

    for step in result["steps"]:
        if step["type"] == "subway":
            arrivals = get_subway_realtime(step.get("realtime_station", ""))
            if arrivals:
                step["realtimeArrivals"] = arrivals[:3]
        elif step["type"] == "bus" and step.get("station_id"):
            arrivals = get_bus_realtime(step["station_id"])
            if arrivals:
                step["realtimeArrivals"] = arrivals[:3]

    return jsonify(result)

@app.route("/api/subway/realtime", methods=["GET"])
def subway_realtime():
    station = request.args.get("station", "")
    if not station:
        return jsonify({"error": "station 파라미터가 필요합니다."}), 400
    return jsonify({"station": station, "arrivals": get_subway_realtime(station)})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.now().strftime("%H:%M:%S"),
        "apis": {"odsay": bool(ODSAY_API_KEY), "subway": bool(SEOUL_SUBWAY_KEY), "bus": bool(BUS_API_KEY)}
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
