import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - KONEPS - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# G2B 입찰공고 검색에 사용할 키워드 & 카테고리
# ─────────────────────────────────────────────
TARGET_KEYWORDS = [
    {"keyword": "시장조사",   "category": "market"},
    {"keyword": "소비자조사", "category": "consumer"},
    {"keyword": "사용자조사", "category": "user"},
    {"keyword": "UX리서치",   "category": "user"},
    {"keyword": "만족도조사", "category": "consumer"},
    {"keyword": "사회조사",   "category": "social"},
    {"keyword": "패널조사",   "category": "panel"},
    {"keyword": "리서치",     "category": "research"},
]

SEJONG_ORGS = [
    "세종시설관리공단", "세종특별자치시", "세종도시교통공사",
    "세종문화관광재단", "세종테크노파크", "세종스마트시티",
]

# ─────────────────────────────────────────
# G2B 입찰공고 검색 셀렉터 (2026-03 기준)
# ─────────────────────────────────────────
# ── 네비게이션 메뉴 셀렉터 (WebSquare5 프레임워크 기반)
SEL_MENU_BID        = "#mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_btn_menuLvl1"   # 상단 '입찰' 메뉴
SEL_MENU_BID_LIST   = "#mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3"  # '입찰공고목록'

# ── 검색 폼 셀렉터 (입찰공고목록 페이지)
SEL_BID_ANNOUNCE_INPUT  = "#mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm"
SEL_BID_ANNOUNCE_BTN    = "#mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004"
SEL_RESULT_TBODY        = "#mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_tbody"
# 열 인덱스: 4=공고명, 6=수요기관, 7=게시일시/마감일 (실제 렌더 기준)
COL_TITLE    = 4
COL_ORG      = 6
COL_DEADLINE = 7

G2B_URL = "https://www.g2b.go.kr/"


def convert_bid_date(date_str: str) -> str:
    """G2B 날짜 문자열을 ISO 포맷으로 변환합니다."""
    if not date_str:
        return (datetime.now() + timedelta(days=30)).isoformat()
    try:
        date_str = date_str.strip().replace("/", "-")
        if len(date_str) >= 16:
            return datetime.strptime(date_str[:16], "%Y-%m-%d %H:%M").isoformat()
        return datetime.strptime(date_str[:10], "%Y-%m-%d").isoformat()
    except Exception:
        return (datetime.now() + timedelta(days=30)).isoformat()


def dismiss_popups(page):
    """홈 화면 팝업을 닫습니다."""
    try:
        page.wait_for_timeout(2000)
        # 팝업 닫기: ID 패턴 매칭 (팝업 ID는 세션마다 일련번호가 달라지므로 suffix 매칭)
        close_btns = page.query_selector_all("[id*='_close'], [id*='btnClose']")
        for btn in close_btns:
            try:
                if btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(400)
            except Exception:
                pass
        # 추가: 본문에 있는 오늘 하루 닫기 버튼
        page.wait_for_timeout(500)
    except Exception:
        pass


def navigate_to_bid_list(page):
    """G2B 메인 → 입찰 → 입찰공고목록으로 이동합니다."""
    page.goto(G2B_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dismiss_popups(page)

    # 상단 메뉴 "입찰" 클릭 — 안정적인 ID 사용
    try:
        page.click(SEL_MENU_BID, force=True, timeout=10000)
    except Exception:
        # Fallback: 텍스트 기반 클릭 (정확한 nav 영역 내)
        page.locator("#mf_wfm_gnb_wfm_gnbMenu span:has-text('입찰')").first.click(force=True)
    page.wait_for_timeout(1000)

    # 서브메뉴 "입찰공고목록" 클릭
    try:
        page.click(SEL_MENU_BID_LIST, force=True, timeout=8000)
    except Exception:
        page.locator("#mf_wfm_gnb span:has-text('입찰공고목록')").first.click(force=True)
    
    # 검색 입력창이 나타날 때까지 대기
    page.wait_for_selector(SEL_BID_ANNOUNCE_INPUT, timeout=20000)
    page.wait_for_timeout(1500)
    logger.info("입찰공고목록 페이지 진입 성공")


def search_and_collect(page, keyword: str, category: str) -> list:
    """주어진 키워드로 검색 후 결과 행을 파싱하여 반환합니다."""
    bids = []

    try:
        # 검색창 초기화 (JS로 값 설정 — 한글 IME 문제 우회)
        page.evaluate(
            f"document.querySelector('{SEL_BID_ANNOUNCE_INPUT}').value = '{keyword}'"
        )
        # WebSquare 입력 이벤트 발생 (프레임워크가 변경을 인식하도록)
        page.evaluate(
            f"""
            var el = document.querySelector('{SEL_BID_ANNOUNCE_INPUT}');
            if (el) {{
                el.dispatchEvent(new Event('input', {{bubbles:true}}));
                el.dispatchEvent(new Event('change', {{bubbles:true}}));
            }}
            """
        )
        page.wait_for_timeout(500)

        # 검색 버튼 클릭
        page.click(SEL_BID_ANNOUNCE_BTN, force=True)
        page.wait_for_timeout(4000)

        # 결과 행 수집
        try:
            page.wait_for_selector(f"{SEL_RESULT_TBODY} tr", timeout=7000)
        except PWTimeoutError:
            logger.info(f"  '{keyword}' 검색 결과 없거나 로딩 타임아웃")
            return []

        rows = page.query_selector_all(f"{SEL_RESULT_TBODY} tr")
        logger.info(f"  '{keyword}' 검색 결과: {len(rows)}행")

        for idx, row in enumerate(rows[:30]):  # 최대 30건
            try:
                # 셀을 열 인덱스로 가져오기
                cells = row.query_selector_all("td")
                if len(cells) <= COL_DEADLINE:
                    continue

                title    = cells[COL_TITLE].inner_text().strip()
                org      = cells[COL_ORG].inner_text().strip()
                deadline = cells[COL_DEADLINE].inner_text().strip()

                if not title or title in ("", "-"):
                    continue

                bids.append({
                    "id":           f"g2b-{abs(hash(title + org))}",
                    "title":        title,
                    "organization": org,
                    "start":        datetime.now().isoformat(),
                    "deadline":     convert_bid_date(deadline),
                    "category":     category,
                    "source":       "gov",
                    "url":          G2B_URL,
                    "description":  f"수요기관: {org} | 나라장터 입찰공고목록 '{keyword}' 검색 결과",
                })
            except Exception as e:
                logger.debug(f"  행 파싱 오류 (row {idx}): {e}")
                continue

    except Exception as e:
        logger.error(f"  '{keyword}' 검색 중 오류: {e}")

    return bids


def perform_ui_scrape(keywords_list: list, is_sejong: bool = False) -> list:
    """
    Playwright로 G2B 입찰공고목록을 검색하여 입찰 데이터를 수집합니다.
    - is_sejong=True 이면 수요기관명에 세종 관련 기관이 포함된 것만 필터링합니다.
    """
    all_bids = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        page = context.new_page()

        try:
            navigate_to_bid_list(page)
        except Exception as e:
            logger.error(f"입찰공고목록 페이지 이동 실패: {e}\n{traceback.format_exc()}")
            browser.close()
            return []

        for kw_info in keywords_list:
            keyword  = kw_info["keyword"]
            category = kw_info["category"]

            logger.info(f"UI 스크래핑 검색 중: {keyword}")
            bids = search_and_collect(page, keyword, category)

            # 세종 필터링
            if is_sejong:
                bids = [
                    b for b in bids
                    if any(org in b.get("organization", "") for org in SEJONG_ORGS)
                    or "세종" in b.get("organization", "")
                ]

            all_bids.extend(bids)
            page.wait_for_timeout(800)  # 요청 간 인터벌

        browser.close()

    # 중복 제거 (title + org 기준)
    seen = {}
    for b in all_bids:
        key = b["title"] + b["organization"]
        if key not in seen:
            seen[key] = b
    unique = list(seen.values())
    logger.info(f"총 {len(unique)}건의 입찰 정보를 수집했습니다.")
    return unique


# ──────────────────────────────
# 공개 함수 (update_calendar_bids.py 에서 import)
# ──────────────────────────────

def fetch_bids_from_koneps() -> list:
    logger.info("조달청 나라장터 리서치 입찰 정보 UI 수집을 시작합니다.")
    return perform_ui_scrape(TARGET_KEYWORDS, is_sejong=False)


def fetch_sejong_bids_from_koneps() -> list:
    logger.info("세종시 산하기관 조달청 입찰 정보 UI 수집을 시작합니다.")
    sejong_keywords = [{"keyword": "세종", "category": "sejong"}]
    return perform_ui_scrape(sejong_keywords, is_sejong=True)


# ──────────────────────────────
# 단독 실행 (테스트용)
# ──────────────────────────────
if __name__ == "__main__":
    result = fetch_bids_from_koneps()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n총 {len(result)}건 수집")
