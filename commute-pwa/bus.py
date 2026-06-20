import requests
from config import BUS_API_KEY

BUS_URL = "http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRouteAll"

def get_bus_arrival(station_id: str, bus_route_id: str):
    """정류장 ID와 버스 노선 ID로 실시간 도착 정보 조회"""
    params = {
        "serviceKey": BUS_API_KEY,
        "stId": station_id,
        "busRouteId": bus_route_id,
        "ord": "1",
        "_type": "json"
    }
    try:
        res = requests.get(BUS_URL, params=params, timeout=5)
        data = res.json()
        items = (
            data.get("msgBody", {})
                .get("itemList", [])
        )
        if isinstance(items, dict):
            items = [items]
        arrivals = []
        for item in items:
            arrivals.append({
                "busNo": item.get("rtNm", ""),
                "arrmsg1": item.get("arrmsg1", ""),  # 첫번째 버스 도착 메시지
                "arrmsg2": item.get("arrmsg2", ""),  # 두번째 버스 도착 메시지
                "vehId1": item.get("vehId1", ""),
                "plainNo1": item.get("plainNo1", ""),
            })
        return arrivals
    except Exception as e:
        return {"error": str(e)}


def parse_arrival_min(arrmsg: str) -> int:
    """도착 메시지에서 분 단위 숫자 추출. 예: '3분후[2번째 전]' → 3"""
    import re
    match = re.search(r"(\d+)분", arrmsg)
    if match:
        return int(match.group(1))
    if "곧 도착" in arrmsg or "0분" in arrmsg:
        return 0
    return 999
