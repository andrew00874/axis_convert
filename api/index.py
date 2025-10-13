# api/index.py
from fastapi import FastAPI, HTTPException
import pyproj

# FastAPI 앱 생성
app = FastAPI()

# 좌표계 정의
KATEC = "+proj=tmerc +lat_0=38N +lon_0=128E +ellps=bessel +x_0=400000 +y_0=600000 +k=0.9999 +units=m +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43"
WGS84 = "+proj=latlong +datum=WGS84 +ellps=WGS84"

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