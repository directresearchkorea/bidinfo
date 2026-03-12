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

def fetch_bids_from_koneps():
    """
    나라장터 API를 통해 최근 7일 내 공고된 관련 입찰 정보를 가져옵니다.
    API Key 설정이 필요하므로 현재는 안내 로그를 남기거나 더미 데이터를 반환할 수 있도록 합니다.
    """
    logger.info("조달청 나라장터 리서치 입찰 정보 수집을 시작합니다.")
    
    if not KONEPS_API_KEY or KONEPS_API_KEY == "your_koneps_api_key_here":
        logger.warning("KONEPS_API_KEY가 설정되지 않았습니다. API를 이용하시려면 공공데이터포털(data.go.kr)에서 발급받으세요.")
        logger.warning("테스트용 더미 데이터를 반환합니다.")
        return mock_koneps_data()

    # Calculate date range: Today to +12 weeks (미리 준비할 수 있도록 마감일 기준 검색)
    start_date = datetime.now()
    end_date = start_date + timedelta(weeks=12)
    
    inqryBgnDt = start_date.strftime("%Y%m%d%H%M")
    inqryEndDt = end_date.strftime("%Y%m%d%H%M")
    
    bids = []
    
    for kw in TARGET_KEYWORDS:
        keyword = kw['keyword']
        category = kw['category']
        
        # NOTE: 실제로 inqryDiv, inqryBgnDt 파라미터와 함께 bidNm(입찰건명)으로 검색하거나 통으로 가져와 필터링해야할 수도 있습니다.
        # 공공데이터 API 상세 스펙에 맞게 payload 조정 필요
        params = {
            'serviceKey': KONEPS_API_KEY,
            'numOfRows': '50',
            'pageNo': '1',
            'inqryDiv': '2', # 2: 입찰마감일시 검색 (미래의 공고를 찾기 위함)
            'inqryBgnDt': inqryBgnDt,
            'inqryEndDt': inqryEndDt,
            'bidNm': keyword,  # Some APIs support this, otherwise client-side filtering needed
            'type': 'json'
        }
        
        try:
            response = requests.get(KONEPS_BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('response', {}).get('body', {}).get('items', [])
                
                # If structure is different, handle it gracefully
                if isinstance(items, list):
                    for item in items:
                        # Map to common schema
                        bid_no = item.get('bidNtceNo', '')
                        bid_ord = item.get('bidNtceOrd', '0')
                        bid_url = f"https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno={bid_no}&bidseq={bid_ord}" if bid_no else "https://www.g2b.go.kr"
                        
                        bids.append({
                            'id': bid_no + '-' + bid_ord,
                            'title': item.get('bidNtceNm', '제목 없음'),
                            'organization': item.get('ntceInsttNm', '기관명 없음'),
                            'deadline': convert_koneps_date(item.get('bidClseDt', '')),
                            'category': category,
                            'source': 'gov',
                            'url': bid_url, # 나라장터 상세 링크 직접 생성
                            'description': f"공고일자: {item.get('bidNtceDt', '')} / 수요기관: {item.get('dminsttNm', '')} / 기초금액: {item.get('presmptPrce', 0)}원\n\n조달청 나라장터 공고 내용입니다."
                        })
            else:
                logger.error(f"API Error ({response.status_code}) for keyword: {keyword}")
        except Exception as e:
            logger.error(f"Failed to fetch data for keyword '{keyword}': {e}")
            
    # 중복 ID 제거
    unique_bids = {b['id']: b for b in bids}.values()
    return list(unique_bids)

def convert_koneps_date(date_str):
    """ 'YYYY-MM-DD HH:MM:SS' 혹은 'YYYYMMDDHHMMSS' 기반 변환 """
    if not date_str:
        return datetime.now().isoformat()
    # Simple format handler logic here
    try:
        if len(date_str) == 14:
            d = datetime.strptime(date_str, "%Y%m%d%H%M%S")
        else:
            d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return d.isoformat()
    except:
        return datetime.now().isoformat()

def mock_koneps_data():
    now = datetime.now()
    return [
        {
            "id": f"gov-test-{int(now.timestamp())}-1",
            "title": "[API 테스트] 2026년 공공 모빌리티 서비스(MaaS) 시민 이용 실태조사 및 소비자 인식조사",
            "organization": "한국교통안전공단",
            "deadline": (now + timedelta(weeks=10)).isoformat(), # +10 weeks example
            "category": "consumer",
            "source": "gov",
            "url": "https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno=20240100000&bidseq=00",
            "description": "다이렉트 리서치 코리아를 위한 테스트 공고문입니다.\n마감일이 +12주 내에 있는 입찰 데이터를 시뮬레이션 합니다 (API 미연동 모의데이터)."
        }
    ]

def fetch_sejong_bids_from_koneps():
    """
    세종시 및 주요 산하기관에서 발주하는 조달청 입찰 공고를 실시간으로 검색합니다.
    (세종도시교통공사, 세종시문화재단 등)
    """
    logger.info("세종시 산하기관 조달청 입찰 정보 수집을 시작합니다.")
    
    if not KONEPS_API_KEY or KONEPS_API_KEY == "your_koneps_api_key_here":
        return mock_sejong_data()

    start_date = datetime.now()
    end_date = start_date + timedelta(weeks=12)
    inqryBgnDt = start_date.strftime("%Y%m%d%H%M")
    inqryEndDt = end_date.strftime("%Y%m%d%H%M")
    
    bids = []
    
    # ntceInsttNm(공고기관명/수요기관명) 검색 파라미터 (세종 키워드 하나로 묶어 검색)
    params = {
        'serviceKey': KONEPS_API_KEY,
        'numOfRows': '50',
        'pageNo': '1',
        'inqryDiv': '2',
        'inqryBgnDt': inqryBgnDt,
        'inqryEndDt': inqryEndDt,
        'ntceInsttNm': '세종',  # 세종시, 세종도시교통공사 등 포괄 검색
        'type': 'json'
    }
    
    try:
        response = requests.get(KONEPS_BASE_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            
            if isinstance(items, list):
                for item in items:
                    bid_no = item.get('bidNtceNo', '')
                    bid_ord = item.get('bidNtceOrd', '0')
                    bid_url = f"https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno={bid_no}&bidseq={bid_ord}" if bid_no else "https://www.g2b.go.kr"
                    
                    bids.append({
                        'id': bid_no + '-' + bid_ord + '-s',
                        'title': item.get('bidNtceNm', '제목 없음'),
                        'organization': item.get('ntceInsttNm', '기관명 없음'),
                        'deadline': convert_koneps_date(item.get('bidClseDt', '')),
                        'category': 'sejong',
                        'source': 'gov',
                        'url': bid_url,
                        'description': f"공고일자: {item.get('bidNtceDt', '')} / 수요기관: {item.get('dminsttNm', '')}\n\n세종시 공공기관 조달청 입찰 공고 내용입니다."
                    })
        else:
            logger.error(f"API Error ({response.status_code}) for Sejong institutions")
    except Exception as e:
        logger.error(f"Failed to fetch Sejong data: {e}")
            
    # 중복 ID 제거 (같은 공고가 리서치/세종 양쪽에 겹칠경우 여기서 합쳐지는게 아니라 앱단이나 통합 단계에서 처리됨)
    unique_bids = {b['id']: b for b in bids}.values()
    return list(unique_bids)

def mock_sejong_data():
    now = datetime.now()
    return [
        {
            "id": f"gov-test-{int(now.timestamp())}-s1",
            "title": "[모의] 세종시 시내버스 신규 노선 시민 만족도 리서치",
            "organization": "세종도시교통공사",
            "deadline": (now + timedelta(weeks=2)).isoformat(),
            "category": "sejong",
            "source": "gov",
            "url": "https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno=20240200000&bidseq=00",
            "description": "최근 개편된 대중교통 노선망에 대한 이용 실태조사 및 만족도 리서치 발주 (API 미연동 모의데이터)"
        },
        {
            "id": f"gov-test-{int(now.timestamp())}-s2",
            "title": "[모의] 청소년 스마트기기 과의존 예방 교육 효과성 평가지표 개발 연구",
            "organization": "세종시청소년진흥재단",
            "deadline": (now + timedelta(weeks=5)).isoformat(),
            "category": "sejong",
            "source": "gov",
            "url": "https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno=20240300000&bidseq=00",
            "description": "세종시 내 청소년상담복지센터에서 진행중인 예방 교육에 대한 실효성 및 패널 조사 분석용역. (API 미연동 모의데이터)"
        }
    ]

if __name__ == "__main__":
    result = fetch_bids_from_koneps()
    print(json.dumps(result, ensure_ascii=False, indent=2))
