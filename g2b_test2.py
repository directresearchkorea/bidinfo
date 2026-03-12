from playwright.sync_api import sync_playwright
import time
from datetime import datetime

def convert_koneps_date(date_str):
    if not date_str:
        return datetime.now().isoformat()
    try:
        # e.g., '2026/03/10' or similar
        date_str = date_str.replace('/', '-')
        if len(date_str) == 10:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            d = datetime.strptime(date_str.split(' ')[0], "%Y-%m-%d")
        return d.isoformat()
    except:
        return datetime.now().isoformat()

def test_scrape_g2b_bids_via_ui(search_term="조사"):
    bids = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Navigating to g2b...")
            page.goto("https://www.g2b.go.kr/")
            page.wait_for_timeout(2000)
            
            # Close popup if any
            try:
                for el in page.query_selector_all('span:has-text("오늘 하루 이 창을 열지 않음"), button:has-text("닫기"), a:has-text("닫기"), span:has-text("닫기")'):
                    try: el.click()
                    except: pass
            except: pass
            
            page.wait_for_timeout(1000)
            print("Clicking menu...")
            page.locator('span:has-text("발주")').first.click()
            page.wait_for_timeout(1000)
            page.locator('span:has-text("발주목록")').first.click()
            print("Waiting for input box...")
            page.wait_for_selector('#mf_wfm_container_txtBizNm', timeout=15000)
            
            print("Searching...")
            page.fill('#mf_wfm_container_txtBizNm', search_term)
            page.click('#mf_wfm_container_btnS0001') # search button
            page.wait_for_timeout(3000) # wait for table to update
            
            rows = page.query_selector_all('#mf_wfm_container_gridView1_body_tbody tr')
            for index, r in enumerate(rows[:5]):
                title_td = r.query_selector('td[id$="_column25"] a') 
                title = title_td.inner_text().strip() if title_td else r.inner_text().split("\n")[0]
                
                org_td = r.query_selector('td[id$="_column23"]')
                org = org_td.inner_text().strip() if org_td else ''
                
                date_td = r.query_selector('td[id$="_column17"]')
                date_str = date_td.inner_text().strip() if date_td else ''
                
                deadline_iso = convert_koneps_date(date_str)
                
                print(f"[{index+1}] {title} / {org} / {deadline_iso}")
                
        except Exception as e:
            print(f"UI Scraping Error: {e}")
            page.screenshot(path='g2b_error2.png')
            
        browser.close()

if __name__ == "__main__":
    test_scrape_g2b_bids_via_ui()
