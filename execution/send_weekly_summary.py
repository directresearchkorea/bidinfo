import os
import sys
import json
import logging
from datetime import datetime

# sys.path 설정
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_root)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execution.send_report import send_update_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - WEEKLY_SUMMARY - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_event_data_js():
    target_file = os.path.join(_root, 'event_data.js')
    if not os.path.exists(target_file):
        logger.error(f"{target_file} 파일이 없습니다.")
        return []
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # "const bidEvents = [...];" 형태에서 JSON 배열 부분 추출
    try:
        json_str = content.split('=', 1)[1].strip()
        if json_str.endswith(';'):
            json_str = json_str[:-1]
        
        events = json.loads(json_str)
        return events
    except Exception as e:
        logger.error(f"event_data.js 파싱 실패: {e}")
        return []

def generate_weekly_summary():
    events = parse_event_data_js()
    if not events:
        return "데이터가 전혀 없습니다."

    # 통계 합계 구하기
    stats = {}
    for event in events:
        cat = event.get('category', 'unknown')
        stats[cat] = stats.get(cat, 0) + 1
    
    # 마감이 임박한 순서대로 상위 10개 추출
    now_iso = datetime.now().isoformat()
    # 진행중인 건만 필터링
    valid_events = [e for e in events if e.get('deadline') and e['deadline'] > now_iso]
    valid_events.sort(key=lambda x: x['deadline'])
    top_upcoming = valid_events[:10]
    
    # 이메일 내용 조립
    total_count = len(events)
    valid_count = len(valid_events)
    
    content = f"총 {total_count}건의 입찰/전시회 정보가 수집되어 있으며, 이 중 마감일이 지나지 않은 진행 중인 정보는 {valid_count}건 입니다.\n\n"
    content += "[카테고리별 현황]\n"
    for cat, count in stats.items():
        content += f" - {cat}: {count}건\n"
    
    content += "\n[🔥 마감 임박 주요 10건]\n"
    for i, e in enumerate(top_upcoming, 1):
        deadline = e['deadline'][:10] # YYYY-MM-DD
        content += f"{i}. [{deadline}] {e['title'][:40]}... / {e['organization']}\n"
    
    content += "\n--------------------------------------------------\n"
    content += "전체 일정 보기 (캘린더 대시보드 접속 링크):\n"
    content += "👉 https://directresearchkorea.github.io/bidinfo/\n"
    content += "--------------------------------------------------\n"

    return content

if __name__ == "__main__":
    logger.info("주간 요약 메일 생성을 시작합니다.")
    summary_text = generate_weekly_summary()
    
    subject = f"[{datetime.now().strftime('%m/%d')} 위클리] 다이렉트리서치 주간 입찰/행사 요약 리포트"
    body_prefix = "다이렉트 리서치 코리아팀을 위한 이번 주 주요 입찰 및 행사 리스트 요약본입니다."
    
    target_email = "yourfriendjay@gmail.com"
    
    try:
        send_update_report(summary_text, receiver=target_email, subject=subject, body_prefix=body_prefix)
        logger.info(f"{target_email}로 주간 요약 메일 전송 완료!")
    except Exception as e:
        logger.error(f"주간 요약 메일 전송 실패: {e}")
