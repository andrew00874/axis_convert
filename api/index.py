# api/index.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyproj
import httpx

# FastAPI 앱 생성
app = FastAPI()

# 이 부분이 CORS 에러를 해결합니다.
origins = [
    "http://127.0.0.1:5500", # 로컬 테스트 환경 주소
    "http://localhost:5500",  # 다른 로컬 주소 형식
    "null",                   # 로컬에서 파일을 직접 열었을 때의 origin
    "https://kakao-map-opinet-g-sprice-m9v17fwva-jaeminkims-projects.vercel.app"
    # 나중에 실제 웹사이트를 배포한다면 그 주소도 추가해줘야 합니다.
    # 예: "https://my-awesome-map-project.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # origins 리스트에 있는 주소에서의 요청을 허용합니다.
    allow_credentials=True,      # 쿠키를 포함한 요청을 허용합니다.
    allow_methods=["*"],         # 모든 HTTP 메소드를 허용합니다. (GET, POST 등)
    allow_headers=["*"],         # 모든 HTTP 헤더를 허용합니다.
)
# --- CORS 설정 끝 ---

# 좌표계 정의
WGS84 = "+proj=latlong +datum=WGS84 +ellps=WGS84"
KATEC = "+proj=tmerc +lat_0=38N +lon_0=128E +ellps=bessel +x_0=400000 +y_0=600000 +k=0.9999 +units=m +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43"
# CRS 객체 생성
KATEC_proj = pyproj.CRS(KATEC)
WGS84_proj = pyproj.CRS(WGS84)

# 1. 변환기: KATEC -> WGS84 (순방향)
transformer_to_wgs84 = pyproj.Transformer.from_crs(KATEC_proj, WGS84_proj, always_xy=True)

# 2. 변환기: WGS84 -> KATEC (역방향)
transformer_to_katec = pyproj.Transformer.from_crs(WGS84_proj, KATEC_proj, always_xy=True)


# --- API 엔드포인트 정의 ---

@app.get("/")
def read_root():
    return {
        "message": "Coordinate Conversion API",
        "endpoints": [
            "/katec-to-wgs84?x={x_coord}&y={y_coord}",
            "/wgs84-to-katec?lon={longitude}&lat={latitude}"
        ]
    }

@app.get("/katec-to-wgs84")
def convert_katec_to_wgs84(x: float, y: float):
    """
    KATEC 좌표(x, y)를 WGS84 경위도(lon, lat)로 변환합니다.
    """
    try:
        lon, lat = transformer_to_wgs84.transform(x, y)
        return {"lon": lon, "lat": lat}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/wgs84-to-katec")
def convert_wgs84_to_katec(lon: float, lat: float):
    """
    WGS84 경위도(lon, lat)를 KATEC 좌표(x, y)로 변환합니다.
    """
    try:
        x, y = transformer_to_katec.transform(lon, lat)
        return {"x": x, "y": y}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# ✅ [추가] Opinet API를 위한 프록시 엔드포인트
@app.get("/api/nearby-gas-stations")
async def get_nearby_gas_stations(x: float, y: float, radius: int = 5000, prodcd: str = "B027"):
    OPINET_API_URL = "https://www.opinet.co.kr/api/aroundAll.do"
    # 중요: 실제 서비스에서는 API 키를 코드에 직접 넣지 않고 환경 변수로 관리하는 것이 안전합니다.
    OPINET_API_KEY = "F250930867" 

    params = {
        "code": OPINET_API_KEY,
        "x": x,
        "y": y,
        "radius": radius,
        "prodcd": prodcd,
        "out": "xml"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPINET_API_URL, params=params)
            response.raise_for_status() # HTTP 에러 발생 시 예외 처리
            # Opinet이 XML을 반환하므로, 그대로 클라이언트에 전달합니다.
            # 하지만 FastAPI는 기본적으로 JSON을 반환하므로, XML을 텍스트로 감싸서 JSON으로 보냅니다.
            return {"xml_data": response.text}
        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail=f"Opinet API 요청 실패: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Opinet API 에러: {exc.response.text}")

@app.get("/api/detailById")
async def detail_by_id(uid: str):
    OPINET_API_URL = "https://www.opinet.co.kr/api/detailById.do"
    # 중요: 실제 서비스에서는 API 키를 코드에 직접 넣지 않고 환경 변수로 관리하는 것이 안전합니다.
    OPINET_API_KEY = "F250930867" 

    params = {
        "code": OPINET_API_KEY,
        "id": uid,
        "out": "xml"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPINET_API_URL, params=params)
            response.raise_for_status() # HTTP 에러 발생 시 예외 처리
            # Opinet이 XML을 반환하므로, 그대로 클라이언트에 전달합니다.
            # 하지만 FastAPI는 기본적으로 JSON을 반환하므로, XML을 텍스트로 감싸서 JSON으로 보냅니다.
            return {"xml_data": response.text}
        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail=f"Opinet API 요청 실패: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Opinet API 에러: {exc.response.text}")