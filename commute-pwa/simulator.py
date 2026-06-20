from datetime import datetime, timedelta
from bus import get_bus_arrival, parse_arrival_min
from subway import get_subway_arrival

def simulate_route(route: dict, depart_now: bool = True) -> dict:
    """
    경로 딕셔너리를 받아 각 스텝별 예상 시각 계산.
    실시간 도착 정보를 반영해 첫 버스/지하철 탑승 시각을 보정.
    """
    now = datetime.now()
    cursor = now
    timeline = []

    steps = route.get("steps", [])
    first_transit = True

    for step in steps:
        t = step.get("type")

        if t == "walk":
            end = cursor + timedelta(minutes=step["time"])
            timeline.append({
                "type": "walk",
                "label": f"도보 {step['time']}분",
                "depart": cursor.strftime("%H:%M"),
                "arrive": end.strftime("%H:%M"),
            })
            cursor = end

        elif t == "bus":
            wait = 0
            if first_transit and step.get("stationID") and step.get("busID"):
                arrivals = get_bus_arrival(step["stationID"], step["busID"])
                if isinstance(arrivals, list) and arrivals:
                    wait = parse_arrival_min(arrivals[0].get("arrmsg1", ""))
                    if wait == 999:
                        wait = 10
                first_transit = False

            board = cursor + timedelta(minutes=wait)
            end = board + timedelta(minutes=step["time"])
            timeline.append({
                "type": "bus",
                "label": f"{step['name']}번 버스",
                "station": step.get("start", ""),
                "endStation": step.get("end", ""),
                "waitMin": wait,
                "depart": board.strftime("%H:%M"),
                "arrive": end.strftime("%H:%M"),
            })
            cursor = end

        elif t == "subway":
            wait = 0
            if step.get("start"):
                arrivals = get_subway_arrival(step["start"])
                if isinstance(arrivals, list) and arrivals:
                    msg = arrivals[0].get("arvlMsg", "")
                    import re
                    m = re.search(r"(\d+)분", msg)
                    wait = int(m.group(1)) if m else 3

            board = cursor + timedelta(minutes=wait)
            end = board + timedelta(minutes=step["time"])
            timeline.append({
                "type": "subway",
                "label": step.get("name", "지하철"),
                "station": step.get("start", ""),
                "endStation": step.get("end", ""),
                "waitMin": wait,
                "depart": board.strftime("%H:%M"),
                "arrive": end.strftime("%H:%M"),
            })
            cursor = end

    arrive_time = cursor
    target = now.replace(hour=10, minute=0, second=0, microsecond=0)
    margin = int((target - arrive_time).total_seconds() / 60)

    return {
        "timeline": timeline,
        "arriveTime": arrive_time.strftime("%H:%M"),
        "marginMin": margin,
        "onTime": margin >= 0
    }


def recommend_depart_time(total_min: int) -> str:
    """10시 도착 기준 역산한 권장 출발 시각"""
    target = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    depart = target - timedelta(minutes=total_min + 5)  # 5분 여유
    return depart.strftime("%H:%M")
