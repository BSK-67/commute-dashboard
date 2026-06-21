export const config = { runtime: "edge" };

const ODSAY_KEY = "mTXJ4RrO4uXr6CAYlN+S3A";
const BUS_KEY   = "8b6717046b2e5e668ab6f70aa22bbd2e5a0e7144e19b350420a5aed88349b545";
const SUBWAY_KEY= "456b774a51716b7337346c66616369";

const SX = 126.8228, SY = 37.5637;
const EX = 126.8824, EY = 37.4810;

const cors = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };

export default async function handler(req) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type");

  try {
    if (type === "route") {
      const url = `https://api.odsay.com/v1/api/searchPubTransPathT?SX=${SX}&SY=${SY}&EX=${EX}&EY=${EY}&apiKey=${encodeURIComponent(ODSAY_KEY)}`;
      const res = await fetch(url);
      const data = await res.json();
      return new Response(JSON.stringify(data), { headers: cors });
    }

    if (type === "bus") {
      const stId = searchParams.get("stId");
      const busRouteId = searchParams.get("busRouteId");
      const url = `https://apis.data.go.kr/6110000/busarrivalservice/getBusArrivalItem?serviceKey=${BUS_KEY}&stId=${stId}&busRouteId=${busRouteId}&ord=1&_type=json`;
      const res = await fetch(url);
      const data = await res.json();
      return new Response(JSON.stringify(data), { headers: cors });
    }

    if (type === "subway") {
      const station = searchParams.get("station");
      const url = `http://swopenAPI.seoul.go.kr/api/subway/${SUBWAY_KEY}/json/realtimeStationArrival/0/5/${encodeURIComponent(station)}`;
      const res = await fetch(url);
      const data = await res.json();
      return new Response(JSON.stringify(data), { headers: cors });
    }

    return new Response(JSON.stringify({ error: "type 파라미터 필요" }), { status: 400, headers: cors });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: cors });
  }
}
