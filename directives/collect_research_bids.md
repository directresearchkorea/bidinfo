# Research Bid Information Collection Directive

**Goal:** 다이렉트 리서치 코리아(Direct Research Korea)를 위한 마켓/컨슈머/유저 리서치 관련 전 세계 및 국내 입찰 정보를 정기적으로 수집하여 캘린더 형태의 UI로 제공한다.

**Target Categories:** 
1. `Market Research` (시장 조사)
2. `Consumer Research` (소비자 조사)
3. `User Research` (사용자 조사 / UI·UX 리서치)

**Data Sources:**
1. **국내 정부/공공기관/국책연구원:** 조달청(나라장터 OpenAPI), 알리오(공공기관), 주요 국책 연구원 공지사항
2. **국내/외 기업:** 글로벌 프리랜서/B2B 플랫폼(Upwork 등), 글로벌 RFP 수집 사이트 등 (추후 확장)

**Data Fields to Collect:**
- 프로젝트명 (리서치 프로젝트)
- 프로젝트 요청 내용 (상세 내용/제안요청서 요약)
- 담당자명 / 부서
- 마감일자 (Deadline)
- 공고 URL

**Outputs:**
- `event_data.js`: 수집된 입찰 정보를 FullCalendar 프론트엔드가 읽을 수 있는 JSON/JS 배열 형태로 저장

**Execution Scripts:**
- `execution/collect_koneps_bids.py`: 조달청(나라장터) OPEN API를 통해 리서치 관련 입찰정보 수집 (키워드: 리서치, 시장조사, 소비자조사, 만족도조사 등)
- `execution/collect_global_rfps.py`: 글로벌 프리랜스 플랫폼 및 주요 리서치 의뢰 사이트에서 리서치 관련 RFP 수집 (Selenium/Playwright 활용)
- `execution/update_calendar_bids.py`: 수집 스크립트들을 실행하고, 통합된 데이터를 바탕으로 `event_data.js` 파일을 갱신하는 메인 오케스트레이터

**Schedule:** 매주 월(Mon), 수(Wed), 금(Fri) 00시 혹은 06시 (Windows Task Scheduler 사용 권장)

**Search Range:**
- 입찰 및 프로젝트 마감일 기준 현재부터 최대 **+12주(약 3개월)** 뒤의 공고까지 미리 검색하여 사전에 준비할 수 있도록 파이프라인을 구성한다.

**Error Handling & Limits:**
- 정부 API 사용 시 Rate Limit 등을 고려하여 호출 간격을 둔다.
- 임시 캐시(`.tmp/bids_cache.json`)에 기존 수집 내역을 캐싱하여, 중복 및 누락을 방지한다.
