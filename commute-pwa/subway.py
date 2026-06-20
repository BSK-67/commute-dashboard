import requests
from config import SUBWAY_API_KEY

SUBWAY_URL = f"http://swopenAPI.seoul.go.kr/api/subway/{SUBWAY_API_KEY}/json/realtimeStationArrival/0/5"

def get_subway_arrival(station_name: str):
    """역 이름으로 실시간 지하철 도착 정보 조회"""
    try:
        url = f"{SUBWAY_URL}/{requests.utils.quote(station_name)}"
        res = requests.get(url, timeout=5)
        data = res.json()
        rows = data.get("realtimeArrivalList", [])
        arrivals = []
        for row in rows:
            arrivals.append({
                "line": row.get("subwayId", ""),
                "trainNo": row.get("btrainNo", ""),
                "arvlMsg": row.get("arvlMsg2", ""),   # 도착 메시지
                "arvlMsg3": row.get("arvlMsg3", ""),  # 몇 번째 전
                "bstatnNm": row.get("bstatnNm", ""),  # 종착역
                "updnLine": row.get("updnLine", ""),  # 상행/하행
                "recptnDt": row.get("recptnDt", ""),  # 수신 시각
            })
        return arrivals
    except Exception as e:
        return {"error": str(e)}
