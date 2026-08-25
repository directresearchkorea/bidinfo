import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

import logging
from execution.db_utils import get_recent_custom_bids
from execution.send_report import send_update_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - WEEKLY REPORT - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("주간 맞춤형 알림 메일 발송을 시작합니다.")
    
    # 지난 7일간 저장된 '게임', '유저', 'ai' 키워드 공고 가져오기
    recent_bids = get_recent_custom_bids(days=7)
    
    if recent_bids:
        content_lines = []
        for i, b in enumerate(recent_bids, 1):
            deadline_str = b.get("deadline", "")
            if deadline_str and len(deadline_str) >= 10:
                deadline_str = deadline_str[:10]
            line = f"{i}. 공고명: {b.get('title', '')}\n   수요기관: {b.get('organization', '')}\n   마감일: {deadline_str}\n   URL: {b.get('url', '')}"
            content_lines.append(line)
            
        report_content = "\n\n".join(content_lines)
        
        try:
            send_update_report(
                content=report_content,
                receiver="yourfriendjay@gmail.com",
                subject=f"[주간 알림] '게임' / '유저' / 'AI' 관련 신규 입찰 공고 ({len(recent_bids)}건)",
                body_prefix="지난 한 주 동안 새롭게 수집된 '게임', '유저', 'AI' 키워드가 포함된 입찰 공고 목록입니다."
            )
            logger.info("주간 맞춤형 알림 메일 전송 성공.")
        except Exception as e:
            logger.error(f"주간 맞춤형 알림 메일 전송 실패: {e}")
    else:
        logger.info("최근 7일간 수집된 해당 키워드의 공고가 없습니다. (빈 메일 발송)")
        try:
            send_update_report(
                content="이번 주에는 조건에 맞는 신규 입찰 공고가 없습니다.",
                receiver="yourfriendjay@gmail.com",
                subject="[주간 알림] '게임' / '유저' / 'AI' 관련 신규 입찰 공고 (0건)",
                body_prefix="지난 한 주 동안 수집된 '게임', '유저', 'AI' 키워드가 포함된 신규 입찰 공고를 확인했으나 새로운 내역이 없습니다."
            )
            logger.info("주간 빈 메일 전송 성공.")
        except Exception as e:
            logger.error(f"주간 빈 메일 전송 실패: {e}")

if __name__ == "__main__":
    main()
