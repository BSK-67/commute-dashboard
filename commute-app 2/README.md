# 출근 경로 안내 앱

도착 목표 시각 기반 대중교통 역산 경로 안내 시스템

## 구조

```
commute-app/
├── backend/
│   ├── app.py            # Flask API 서버
│   ├── requirements.txt
│   └── .env.example      # API 키 템플릿
└── frontend/
    └── index.html        # 모바일 웹 앱
```

## API 키 준비

| API | 발급처 | 용도 |
|-----|--------|------|
| ODsay | https://lab.odsay.com | 경로 탐색, 좌표 검색 |
| 서울 지하철 실시간 | https://data.seoul.go.kr | 지하철 실시간 도착 |
| 버스 실시간 | https://www.data.go.kr | 버스 실시간 도착 |

## 설치 및 실행

### 1. 백엔드

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate.bat   # Windows

# 패키지 설치
pip install -r requirements.txt

# API 키 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 서버 실행
python app.py
# → http://localhost:5000 에서 실행
```

### 2. 프론트엔드

```bash
# 별도 서버 없이 브라우저에서 바로 열기
open frontend/index.html

# 또는 간단한 HTTP 서버 사용
cd frontend
python -m http.server 3000
# → http://localhost:3000 접속
```

## API 명세

### POST /api/route
경로 탐색 및 출발 시각 역산

**Request**
```json
{
  "from": "김포공항역",
  "to": "가산디지털단지역",
  "arriveTime": "09:50",
  "buffer": 10
}
```

**Response**
```json
{
  "departTime": "08:43",
  "arriveTime": "09:50",
  "totalMin": 67,
  "routeMin": 57,
  "bufferMin": 10,
  "transferCount": 1,
  "walkMin": 8,
  "cost": 1650,
  "steps": [
    {
      "type": "walk",
      "time": "08:43",
      "label": "도보 이동",
      "detail": "출발 → 김포공항역",
      "duration": 7,
      "badge": "도보 7분"
    },
    {
      "type": "subway",
      "time": "08:50",
      "label": "5호선 탑승",
      "detail": "김포공항 → 여의도 (6정거장)",
      "duration": 18,
      "badge": "5호선",
      "color": "#996CAC",
      "realtimeArrivals": [
        { "direction": "마천 방면", "arrivalMsg": "2분 후", "remainSec": 120 }
      ]
    }
  ]
}
```

### GET /api/subway/realtime?station=여의도
지하철 실시간 도착 단독 조회

## 데이터 흐름

```
사용자 입력 (출발지/도착지/목표시각)
  ↓
① ODsay 좌표 검색 (search_station)
  ↓
② ODsay 경로 탐색 (get_odsay_route)
  ↓
③ 도착 목표시각 - 총소요 - 여유 = 출발시각 역산
  ↓
④ 서울 지하철 실시간 API 보강 (get_subway_realtime)
  ↓
⑤ 타임라인 렌더링
```
