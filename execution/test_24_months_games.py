import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

from execution.send_report import send_update_report
from execution.collect_koneps_bids import call_api, _extract_items

target_keywords = ["게임", "유저"]
all_matches = []

print("Starting 24-month fetch...")
end_date = datetime.now()
start_date = end_date - timedelta(days=730)

current_chunk_start = start_date
date_fmt = "%Y%m%d%H%M"

while current_chunk_start < end_date:
    current_chunk_end = current_chunk_start + timedelta(days=30)
    if current_chunk_end > end_date:
        current_chunk_end = end_date
    
    print(f"Fetching chunk: {current_chunk_start.strftime(date_fmt)} ~ {current_chunk_end.strftime(date_fmt)}")
    
    page = 1
    num_rows = 999
    
    while True:
        body = call_api({
            "numOfRows": num_rows,
            "pageNo": page,
            "bidNtceBgnDt": current_chunk_start.strftime(date_fmt),
            "bidNtceEndDt": current_chunk_end.strftime(date_fmt),
        })

        if not body:
            print("No body returned.")
            break

        items = _extract_items(body)
        total = int(body.get("totalCount") or 0)

        if not items:
            break

        for item in items:
            title = item.get("bidNtceNm") or ""
            if not title:
                continue
                
            if any(k in title for k in target_keywords):
                org = item.get("dmndInsttNm") or item.get("ntceInsttNm") or ""
                deadline = item.get("bidClseDate") or item.get("bidClseDt") or ""
                url = item.get("bidNtceUrl") or "https://www.g2b.go.kr/"
                
                all_matches.append({
                    "title": title,
                    "organization": org,
                    "deadline": deadline,
                    "url": url,
                    "notice_date": item.get("bidNtceDt", "")
                })

        collected = page * num_rows
        if collected >= total or len(items) < num_rows:
            break
        page += 1
        time.sleep(0.3)
        
    current_chunk_start = current_chunk_end

print(f"Finished fetching. Total matches found: {len(all_matches)}")

# Remove duplicates if any
unique_matches = []
seen = set()
for m in all_matches:
    key = m["title"] + m["organization"]
    if key not in seen:
        seen.add(key)
        unique_matches.append(m)

# Format email
if unique_matches:
    unique_matches.sort(key=lambda x: x.get("notice_date", ""), reverse=True)
    
    content_lines = []
    for i, b in enumerate(unique_matches, 1):
        line = f"{i}. 공고명: {b['title']}\n   수요기관: {b['organization']}\n   공고일시: {b['notice_date']}\n   마감일: {b['deadline'][:10] if b['deadline'] else ''}\n   URL: {b['url']}"
        content_lines.append(line)
        
    content = "\n\n".join(content_lines)
    
    send_update_report(
        content=content,
        receiver="yourfriendjay@gmail.com",
        subject=f"[알림] 과거 24개월 '게임' / '유저' 관련 공고 ({len(unique_matches)}건)",
        body_prefix=f"요청하신 과거 24개월 동안의 '게임' 및 '유저' 관련 입찰 공고 검색 결과입니다. 총 {len(unique_matches)}건이 발견되었습니다."
    )
    print("Email sent.")
else:
    send_update_report(
        content="검색 결과가 없습니다.",
        receiver="yourfriendjay@gmail.com",
        subject="[알림] 과거 24개월 '게임' / '유저' 관련 공고 (0건)",
        body_prefix="요청하신 과거 24개월 동안의 '게임' 및 '유저' 관련 입찰 공고를 검색했으나 결과가 없습니다."
    )
    print("Email sent (empty).")
