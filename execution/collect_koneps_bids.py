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
# API_KEY는 call_api() 내에서 동적으로 읽음 (모듈 import 시점 문제 방지)
BASE_URL = "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
OP_BID   = "getDataSetOpnStdBidPblancInfo"    # 입찰공고목록


# 이 API는 키워드 검색을 지원하지 않음 → 날짜 범위 전체 조회 후 클라이언트 필터링
RESEARCH_KEYWORDS = [
    "시장조사", "소비자조사", "사용자조사", "UX리서치", "UX연구",
    "만족도조사", "사회조사", "패널조사", "리서치", "설문조사",
    "소비자패널", "소비자분석", "사용성평가", "사용자경험",
    "market research", "consumer research", "user research",
]

KEYWORD_CATEGORY_MAP = {
    "시장조사": "market", "소비자조사": "consumer", "사용자조사": "user",
    "UX리서치": "user", "UX연구": "user", "만족도조사": "consumer",
    "사회조사": "social", "패널조사": "panel", "리서치": "research",
    "설문조사": "consumer", "소비자패널": "panel", "소비자분석": "consumer",
    "사용성평가": "user", "사용자경험": "user",
    "market research": "market", "consumer research": "consumer", "user research": "user",
}

SEJONG_ORGS = [
    "세종특별자치시", "세종시", "세종도시교통공사", "세종시설관리공단",
    "세종문화관광재단", "세종테크노파크", "세종스마트시티", "세종",
]


def _parse_date(date_str: str) -> str:
    """API 날짜 문자열 '202603101530' 또는 '20260310' → ISO 형식"""
    if not date_str:
        return (datetime.now() + timedelta(days=30)).isoformat()
    s = date_str.strip().replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
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


def _contains_research(item: dict) -> bool:
    """아이템이 리서치 관련 입찰인지 키워드 체크"""
    searchable = " ".join([
        item.get("bidNtceNm", ""),
        item.get("ntceInsttNm", ""),
        item.get("dmndInsttNm", ""),
    ]).lower()
    return any(kw.lower() in searchable for kw in RESEARCH_KEYWORDS)


def call_api(params: dict) -> dict | None:
    """나라장터 공공데이터개방표준서비스 API 호출"""
    url = f"{BASE_URL}/{OP_BID}"
    api_key = os.getenv("KONEPS_API_KEY", "")  # 매 호출마다 동적으로 읽음
    if not api_key:
        logger.warning("KONEPS_API_KEY 환경변수가 설정되지 않았습니다.")
        return None
    base_params = {
        "serviceKey": api_key,
        "type": "json",
    }

    base_params.update(params)

    try:
        resp = requests.get(url, params=base_params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            # 실제 응답 구조: {"response": {"header": {...}, "body": {"items": [...], ...}}}
            response_root = data.get("response") or data
            header = response_root.get("header") or {}
            result_code = str(header.get("resultCode") or "")
            if result_code not in ("", "00", "0", "000", "200"):
                logger.warning(f"API 오류 코드 {result_code}: {header.get('resultMsg', '')}")
                return None
            body = response_root.get("body") or {}
            return body
        else:
            logger.warning(f"API HTTP 오류: {resp.status_code}")
            return None
    except Exception as e:
        logger.error(f"API 호출 실패: {e}")
        return None


def _extract_items(body: dict) -> list:
    """body에서 item 리스트를 안전하게 추출
    
    실제 응답: body.items 가 list 또는 dict(단건)로 옴
    """
    items_raw = body.get("items") or []
    if isinstance(items_raw, list):
        return items_raw
    if isinstance(items_raw, dict):
        # 단건인 경우 {bidNtceNo: ..., bidNtceNm: ...}
        # 또는 중첩된 경우 {item: [...]}
        if "item" in items_raw:
            inner = items_raw["item"]
            return [inner] if isinstance(inner, dict) else (inner or [])
        return [items_raw]  # 단건 dict 자체
    return []


def fetch_bids_from_koneps() -> list:
    """
    나라장터 Open API로 현재 ~ 12주 후 전체 입찰공고를 조회하고,
    리서치 관련 키워드가 포함된 건만 필터링하여 반환합니다.
    """
    logger.info("조달청 나라장터 Open API 입찰공고 수집을 시작합니다.")

    today     = datetime.now()
    start_date = today - timedelta(days=30)   # 30일 전부터 현재 활성 공고 포함
    end_date  = today + timedelta(weeks=12)   # 최대 12주 앞까지
    date_fmt  = "%Y%m%d%H%M"

    all_bids = []
    page = 1
    num_rows = 100

    while True:
        body = call_api({
            "numOfRows": num_rows,
            "pageNo": page,
            "bidNtceBgnDt": start_date.strftime(date_fmt),
            "bidNtceEndDt": end_date.strftime(date_fmt),
        })

        if not body:
            logger.warning("API 응답이 없습니다. 수집을 중단합니다.")
            break

        items = _extract_items(body)
        total = int(body.get("totalCount") or body.get("numOfRows") or 0)

        if not items:
            logger.info(f"  페이지 {page}: 데이터 없음 (total={total})")
            break

        # 리서치 키워드 필터링
        filtered = [i for i in items if _contains_research(i)]
        logger.info(f"  페이지 {page}: {len(items)}건 조회 → {len(filtered)}건 리서치 관련 필터링")

        for item in filtered:
            title    = item.get("bidNtceNm") or ""
            org      = item.get("dmndInsttNm") or item.get("ntceInsttNm") or ""
            deadline = item.get("bidClseDt") or item.get("opengDt") or ""
            bid_no   = item.get("bidNtceNo") or ""
            url_link = f"https://www.g2b.go.kr/pt/menu/selectSubMenu.do?menuId=PT02010101000"

            all_bids.append({
                "id":           f"g2b-api-{abs(hash(bid_no + title))}",
                "title":        title,
                "organization": org,
                "start":        today.isoformat(),
                "deadline":     _parse_date(deadline),
                "category":     _keyword_to_category(title),
                "source":       "gov",
                "url":          url_link,
                "description":  f"수요기관: {org} | 공고번호: {bid_no}",
            })

        fetched_so_far = page * num_rows
        if fetched_so_far >= total or len(items) < num_rows:
            break

        page += 1
        time.sleep(0.5)

    # 중복 제거
    seen = {}
    for b in all_bids:
        key = b["title"] + b["organization"]
        if key not in seen:
            seen[key] = b
    unique = list(seen.values())
    logger.info(f"나라장터 API 총 {len(unique)}건 수집 완료 (중복 제거 후)")
    return unique


def fetch_sejong_bids_from_koneps() -> list:
    """
    나라장터 Open API로 전체 입찰공고를 조회한 후,
    수요기관명에 '세종' 관련 키워드가 포함된 건 필터링.
    """
    logger.info("세종시 산하기관 입찰공고 수집을 시작합니다.")

    today    = datetime.now()
    end_date = today + timedelta(weeks=12)
    date_fmt = "%Y%m%d%H%M"

    body = call_api({
        "numOfRows": 100,
        "pageNo": 1,
        "bidNtceBgnDt": today.strftime(date_fmt),
        "bidNtceEndDt": end_date.strftime(date_fmt),
    })

    if not body:
        logger.warning("세종 수집: API 응답 없음")
        return []

    items = _extract_items(body)
    sejong_bids = []

    for item in items:
        org = item.get("dmndInsttNm") or item.get("ntceInsttNm") or ""
        if not any(s in org for s in SEJONG_ORGS):
            continue

        title    = item.get("bidNtceNm") or ""
        deadline = item.get("bidClseDt") or ""
        bid_no   = item.get("bidNtceNo") or ""

        sejong_bids.append({
            "id":           f"g2b-sejong-{abs(hash(bid_no + title))}",
            "title":        title,
            "organization": org,
            "start":        today.isoformat(),
            "deadline":     _parse_date(deadline),
            "category":     "sejong",
            "source":       "gov",
            "url":          "https://www.g2b.go.kr/",
            "description":  f"세종시 산하기관 입찰 | 수요기관: {org} | 공고번호: {bid_no}",
        })

    logger.info(f"세종시 산하기관 입찰 {len(sejong_bids)}건 수집 완료")
    return sejong_bids


# ─────────────────────────────────────────────
# 단독 실행 (테스트)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    result = fetch_bids_from_koneps()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n총 {len(result)}건 수집")
