import os
import json
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - KONEPS - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Search Configuration
KONEPS_API_KEY = os.getenv("KONEPS_API_KEY")
KONEPS_BASE_URL = "http://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoServc04"

# 리서치 관련 키워드 스코프
TARGET_KEYWORDS = [
    {"keyword": "시장조사", "category": "market"},
    {"keyword": "소비자", "category": "consumer"},
    {"keyword": "사용자", "category": "user"},
    {"keyword": "UX", "category": "user"},
    {"keyword": "만족도", "category": "consumer"},
    {"keyword": "사회조사", "category": "social"},
    {"keyword": "패널", "category": "panel"},
    {"keyword": "조사", "category": "research"},
]

from playwright.sync_api import sync_playwright

def convert_koneps_date(date_str):
    if not date_str:
        return datetime.now().isoformat()
    try:
        # Expected format from UI: '2026/03/10' or '2026/03/10 14:00'
        date_str = date_str.replace('/', '-')
        if len(date_str) > 10:
            d = datetime.strptime(date_str[:16], "%Y-%m-%d %H:%M")
        else:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return d.isoformat()
    except:
        return datetime.now().isoformat()

def perform_ui_scrape(keywords_list, is_sejong=False):
    """
    Playwright를 사용하여 "발주" 메뉴의 "발주목록"에서 지정된 키워드/기관으로 검색합니다.
    """
    bids = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            page.goto('https://www.g2b.go.kr/')
            page.wait_for_timeout(2000)
            
            # Dismiss popups
            try:
                for el in page.query_selector_all('span:has-text("오늘 하루 이 창을 열지 않음"), button:has-text("닫기"), a:has-text("닫기"), span:has-text("닫기")'):
                    try: el.click(force=True)
                    except: pass
            except: pass
            
            page.wait_for_timeout(1000)
            
            # Click 발주 menu
            page.locator("span:has-text('발주')").first.click(force=True)
            page.wait_for_timeout(1000)
            page.locator("span:has-text('발주목록')").first.click(force=True)
            
            page.wait_for_selector("#mf_wfm_container_txtBizNm", timeout=15000)
            
            for keyword_info in keywords_list:
                keyword = keyword_info['keyword']
                category = keyword_info['category']
                search_term = keyword
                
                logger.info(f"UI 스크래핑 검색 중: {search_term}")
                
                # Clear and fill the search bar depending on whether we search by business name or org name
                # As observed, #mf_wfm_container_txtBizNm is for Business Name
                if is_sejong:
                    # If sejong, we might type '세종' into the organization input
                    # For simplicity, if we don't know the exact org input selector, we can search '세종' in business name
                    # or filter results. But let's just search '세종' in Business Name or assume '세종' is passed.
                    pass
                
                # Use standard '사업명' search
                page.fill("#mf_wfm_container_txtBizNm", search_term)
                page.click("#mf_wfm_container_btnS0001", force=True) # Search button
                page.wait_for_timeout(3000)
                
                try:
                    page.wait_for_selector("#mf_wfm_container_gridView1_body_tbody tr", timeout=5000)
                    rows = page.query_selector_all("#mf_wfm_container_gridView1_body_tbody tr")
                except:
                    rows = []
                    
                for idx, r in enumerate(rows):
                    if idx >= 20:
                        break
                    title_td = r.query_selector('td[id$="_column25"] a')
                    if not title_td: continue
                    title = title_td.inner_text().strip()
                    
                    org_td = r.query_selector('td[id$="_column23"]')
                    org = org_td.inner_text().strip() if org_td else '기관명 없음'
                    
                    if is_sejong and '세종' not in org:
                        continue # Filter by '세종' organization if needed
                    
                    date_td = r.query_selector('td[id$="_column17"]')
                    date_str = date_td.inner_text().strip() if date_td else ''
                    
                    deadline_iso = convert_koneps_date(date_str)
                    
                    bids.append({
                        'id': f"g2b-ui-{hash(title+org)}",
                        'title': title,
                        'organization': org,
                        'deadline': deadline_iso,
                        'category': category,
                        'source': 'gov',
                        'url': 'https://www.g2b.go.kr/ (검색 발췌)',
                        'description': f"수요기관: {org}\n나라장터 발주목록에서 '{search_term}' 검색으로 발취한 내역입니다."
                    })
                    
        except Exception as e:
            logger.error(f"UI Scraping Failed: {e}")
            
        browser.close()
        
    unique_bids = {b['title'] + b['organization']: b for b in bids}.values()
    return list(unique_bids)

def fetch_bids_from_koneps():
    logger.info("조달청 나라장터 리서치 입찰 정보 UI 수집을 시작합니다.")
    return perform_ui_scrape(TARGET_KEYWORDS, is_sejong=False)

def fetch_sejong_bids_from_koneps():
    logger.info("세종시 산하기관 조달청 입찰 정보 UI 수집을 시작합니다.")
    sejong_keywords = [
        {"keyword": "세종", "category": "sejong"}
    ]
    return perform_ui_scrape(sejong_keywords, is_sejong=True)

if __name__ == "__main__":
    result = fetch_bids_from_koneps()
    print(json.dumps(result, ensure_ascii=False, indent=2))

