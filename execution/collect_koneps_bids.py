import os
import json
import logging
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일을 스크립트 위치 기준으로 명시적으로 로드 (cwd 무관하게 동작)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
load_dotenv(os.path.join(_project_root, ".env"))

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - KONEPS - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# 공공데이터포털 나라장터 공공데이터개방표준서비스 API
# Data: https://www.data.go.kr/data/15058815/openapi.do
# ─────────────────────────────────────────────────────────
BASE_URL = "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
OP_BID   = "getDataSetOpnStdBidPblancInfo"

# ─────────────────────────────────────────────────────────
# 리서치 관련 검색 키워드  (API의 bidNtceNm 파라미터로 직접 검색)
# ─────────────────────────────────────────────────────────
TARGET_KEYWORDS = [
    {"keyword": "시장조사",   "category": "market"},
    {"keyword": "소비자조사", "category": "consumer"},
    {"keyword": "사용자조사", "category": "user"},
    {"keyword": "UX리서치",   "category": "user"},
    {"keyword": "만족도조사", "category": "consumer"},
    {"keyword": "사회조사",   "category": "social"},
    {"keyword": "패널조사",   "category": "panel"},
    {"keyword": "리서치",     "category": "research"},
    {"keyword": "설문조사",   "category": "consumer"},
    {"keyword": "전시회",     "category": "exhibition"},
    {"keyword": "행사",       "category": "event"},
]

SEJONG_ORGS = [
    "세종특별자치시", "세종시", "세종도시교통공사", "세종시설관리공단",
    "세종문화관광재단", "세종테크노파크", "세종스마트시티",
]

KEYWORD_CATEGORY_MAP = {
    "시장조사": "market", "소비자조사": "consumer", "사용자조사": "user",
    "UX리서치": "user", "UX연구": "user", "만족도조사": "consumer",
    "사회조사": "social", "패널조사": "panel", "리서치": "research",
    "설문조사": "consumer", "전시회": "exhibition", "행사": "event",
}


def _parse_date(date_str: str) -> str:
    """API 날짜 문자열 → ISO 8601 형식"""
    if not date_str:
        return (datetime.now() + timedelta(days=30)).isoformat()
    s = date_str.strip().replace("-", "").replace(" ", "").replace(":", "")
    try:
        if len(s) >= 12:
            return datetime.strptime(s[:12], "%Y%m%d%H%M").isoformat()
        if len(s) >= 8:
            return datetime.strptime(s[:8], "%Y%m%d").isoformat()
    except Exception:
        pass
    return (datetime.now() + timedelta(days=30)).isoformat()


def _keyword_to_category(title: str) -> str:
    for kw, cat in KEYWORD_CATEGORY_MAP.items():
        if kw.lower() in title.lower():
            return cat
    return "research"


def _decode_response(resp) -> dict:
    """응답 bytes를 올바른 인코딩으로 디코딩하여 dict 반환"""
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            return json.loads(resp.content.decode(enc))
        except (UnicodeDecodeError, ValueError):
            continue
    return {}


def call_api(params: dict) -> dict | None:
    """나라장터 공공데이터개방표준서비스 API 호출"""
    url = f"{BASE_URL}/{OP_BID}"
    api_key = os.getenv("KONEPS_API_KEY", "")
    if not api_key:
        logger.warning("KONEPS_API_KEY 환경변수가 설정되지 않았습니다.")
        return None

    base_params = {"serviceKey": api_key, "type": "json"}
    base_params.update(params)

    try:
        resp = requests.get(url, params=base_params, timeout=20)
        if resp.status_code == 200:
            data = _decode_response(resp)
            response_root = data.get("response") or data
            header = response_root.get("header") or {}
            result_code = str(header.get("resultCode") or "")
            if result_code not in ("", "00", "0", "000", "200"):
                logger.warning(f"API 오류 코드 {result_code}")
                return None
            body = response_root.get("body") or {}
            return body
        else:
            logger.warning(f"API HTTP 오류: {resp.status_code}")
            return None
    except Exception as e:
        import traceback
        logger.error(f"API 호출 실패: {e}\n{traceback.format_exc()}")
        return None


def _extract_items(body: dict) -> list:
    """body에서 item 리스트를 안전하게 추출"""
    items_raw = body.get("items") or []
    if isinstance(items_raw, list):
        return items_raw
    if isinstance(items_raw, dict):
        inner = items_raw.get("item") or []
        return [inner] if isinstance(inner, dict) else (inner or [])
    return []


def fetch_bids_by_keyword(keyword: str, category: str,
                          start: datetime, end: datetime,
                          max_results: int = 200) -> list:
    """
    나라장터 API에 bidNtceNm 파라미터로 키워드 검색.
    max_results: 키워드당 최대 수집 건수 (기본 200건 제한)
    """
    bids = []
    date_fmt = "%Y%m%d%H%M"
    page = 1
    num_rows = 100  # 페이지당 최대

    while True:
        body = call_api({
            "numOfRows": num_rows,
            "pageNo": page,
            "bidNtceBgnDt": start.strftime(date_fmt),
            "bidNtceEndDt": end.strftime(date_fmt),
            "bidNtceNm": keyword,
        })

        if not body:
            break

        items = _extract_items(body)
        total = int(body.get("totalCount") or 0)

        if not items:
            break

        for item in items:
            title    = item.get("bidNtceNm") or ""
            org      = item.get("dmndInsttNm") or item.get("ntceInsttNm") or ""
            deadline = item.get("bidClseDate") or item.get("bidClseDt") or ""
            bid_no   = item.get("bidNtceNo") or ""
            bid_url  = item.get("bidNtceUrl") or "https://www.g2b.go.kr/"
            ntce_org = item.get("ntceInsttNm") or org

            if not title:
                continue

            bids.append({
                "id":           f"g2b-api-{abs(hash(bid_no + title))}",
                "title":        title,
                "organization": org or ntce_org,
                "start":        datetime.now().isoformat(),
                "deadline":     _parse_date(deadline),
                "category":     _keyword_to_category(title) or category,
                "source":       "gov",
                "url":          bid_url,
                "description":  f"수요기관: {org} | 공고번호: {bid_no}",
            })

        collected = page * num_rows
        logger.info(f"  '{keyword}': {min(collected, total)}/{total}건 (수집 {len(bids)}건)")

        # 최대 건수 제한 또는 마지막 페이지
        if collected >= min(total, max_results) or len(items) < num_rows:
            break
        page += 1
        time.sleep(0.3)

    return bids



def fetch_bids_from_koneps() -> list:
    """전체 리서치 키워드로 나라장터 API 수집"""
    logger.info("조달청 나라장터 Open API 입찰공고 수집을 시작합니다.")
    today = datetime.now()
    start = today - timedelta(days=1)
    end   = today + timedelta(days=30)     # API 허용 범위 내

    all_bids = []
    for kw_info in TARGET_KEYWORDS:
        kw  = kw_info["keyword"]
        cat = kw_info["category"]
        bids = fetch_bids_by_keyword(kw, cat, start, end)
        all_bids.extend(bids)
        time.sleep(0.5)

    # 중복 제거 (title+org 기준)
    seen = {}
    for b in all_bids:
        key = b["title"] + b["organization"]
        if key not in seen:
            seen[key] = b
    unique = list(seen.values())
    logger.info(f"나라장터 API 총 {len(unique)}건 수집 완료 (중복 제거 후)")
    return unique


def fetch_sejong_bids_from_koneps() -> list:
    """세종시 산하기관 입찰 수집 (dmndInsttNm='세종' 키워드로 필터)"""
    logger.info("세종시 산하기관 입찰공고 수집을 시작합니다.")
    today = datetime.now()
    start = today - timedelta(days=1)
    end   = today + timedelta(days=30)
    date_fmt = "%Y%m%d%H%M"

    body = call_api({
        "numOfRows": 100,
        "pageNo": 1,
        "bidNtceBgnDt": start.strftime(date_fmt),
        "bidNtceEndDt": end.strftime(date_fmt),
    })

    if not body:
        return []

    items = _extract_items(body)
    sejong_bids = []
    for item in items:
        org = item.get("dmndInsttNm") or item.get("ntceInsttNm") or ""
        if not any(s in org for s in SEJONG_ORGS):
            continue
        title    = item.get("bidNtceNm") or ""
        deadline = item.get("bidClseDate") or ""
        bid_no   = item.get("bidNtceNo") or ""
        bid_url  = item.get("bidNtceUrl") or "https://www.g2b.go.kr/"
        if not title:
            continue
        sejong_bids.append({
            "id":           f"g2b-sejong-{abs(hash(bid_no + title))}",
            "title":        title,
            "organization": org,
            "start":        datetime.now().isoformat(),
            "deadline":     _parse_date(deadline),
            "category":     "sejong",
            "source":       "gov",
            "url":          bid_url,
            "description":  f"세종시 산하기관 입찰 | 수요기관: {org}",
        })

    logger.info(f"세종시 산하기관 입찰 {len(sejong_bids)}건 수집 완료")
    return sejong_bids


if __name__ == "__main__":
    result = fetch_bids_from_koneps()
    # 출력 시 인코딩 오류 방지
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n총 {len(result)}건 수집")
