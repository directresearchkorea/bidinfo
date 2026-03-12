import os
import json
import logging
from datetime import datetime, timedelta

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - GLOBAL - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_global_rfps():
    """
    해외 프리랜서 풀(Upwork 등) 또는 주요 RFP 수집 사이트에서
    'Market Research', 'Consumer Insight', 'UX Research' 관련
    글로벌 입찰 및 프로젝트 공고를 가져오는 모듈입니다.
    
    *(현재는 시스템 구조화를 위한 Mock-up(더미) 데이터 반환 상태이며, 
    실제 구현 시 Selenium/Playwright 또는 관련 API 연동이 필요합니다.)*
    """
    logger.info("글로벌 리서치 RFP 정보 수집을 시작합니다.")
    
    # 예시 키워드 및 필터 로직이 들어갈 자리
    # search_keywords = ["market research", "consumer research", "user research", "UX research"]
    
    return mock_global_data()

def mock_global_data():
    now = datetime.now()
    return [
        {
            "id": f"global-test-{int(now.timestamp())}-1",
            "title": "[Mock] Global Fintech Market Entry & Consumer Behavior Study",
            "organization": "Confidential (via Upwork)",
            "start": (now + timedelta(days=1)).isoformat(),
            "deadline": (now + timedelta(days=5)).isoformat(),
            "category": "market",
            "source": "global",
            "url": "https://www.upwork.com/freelance-jobs/market-research/",
            "description": "We are a European FinTech startup expanding into South Korea. We need a local market research agency to conduct comprehensive consumer behavior analysis and focus group interviews (FGI)."
        },
        {
            "id": f"global-test-{int(now.timestamp())}-2",
            "title": "[Mock] E-commerce Platform UX Research and Usability Testing",
            "organization": "Global E-Com Inc.",
            "start": (now + timedelta(days=3)).isoformat(),
            "deadline": (now + timedelta(days=10)).isoformat(),
            "category": "user",
            "source": "global",
            "url": "https://www.upwork.com/freelance-jobs/user-research/",
            "description": "Looking for UX researchers based in Korea to conduct moderated usability testing for our newly localized app. 20 participants required."
        }
    ]

if __name__ == "__main__":
    result = fetch_global_rfps()
    print(json.dumps(result, ensure_ascii=False, indent=2))
