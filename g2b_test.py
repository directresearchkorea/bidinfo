from playwright.sync_api import sync_playwright
import time

def scrape_koneps_bids(search_term='조사'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.g2b.go.kr/')
        time.sleep(2)
        
        # Click close popup if any
        try:
            for el in page.query_selector_all('span:has-text("오늘 하루 이 창을 열지 않음"), button:has-text("닫기"), a:has-text("닫기"), span:has-text("닫기")'):
                try: 
                    el.click()
                except: 
                    pass
        except Exception as e:
            print("Popup close error:", e)
            
        time.sleep(1)
        
        try:
            # Click '발주' menu
            page.wait_for_selector('span:has-text("발주")', timeout=10000)
            page.locator('span:has-text("발주")').first.click()
            
            # Submenu '발주목록'
            page.wait_for_selector('span:has-text("발주목록")', timeout=5000)
            page.locator('span:has-text("발주목록")').first.click()
            
            page.wait_for_selector('#mf_wfm_container_txtBizNm', timeout=10000)
            
            # Fill search field
            page.fill('#mf_wfm_container_txtBizNm', search_term)
            
            # Click search button
            page.click('#mf_wfm_container_btnS0001')
            time.sleep(3)
            
            page.wait_for_selector('#mf_wfm_container_gridView1_body_tbody tr', timeout=10000)
            rows = page.query_selector_all('#mf_wfm_container_gridView1_body_tbody tr')
            results = []
            
            for index, r in enumerate(rows[:10]):
                text_content = r.inner_text().replace('\n', ' ')
                results.append(f'[{index}] {text_content}')
                
            print(f'Found {len(results)} results')
            for r in results: 
                print(r)
                
        except Exception as e:
            print('Error scraping:', e)
            page.screenshot(path='g2b_error.png')
            
        browser.close()

if __name__ == '__main__':
    scrape_koneps_bids('조사')
