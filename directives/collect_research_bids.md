# Research Bid Information Collection Directive

**Goal:** 다이렉트 리서치 코리아(Direct Research Korea)를 위한 마켓/컨슈머/유저 리서치 관련 전 세계 및 국내 입찰 정보를 정기적으로 수집하여 캘린더 형태의 UI로 제공한다.

**Target Categories:** 
1. `Market Research` (시장 조사)
2. `Consumer Research` (소비자 조사)
3. `User Research` (사용자 조사 / UI·UX 리서치)

**Data Sources:**
1. **국내 정부/공공기관:** 조달청(나라장터 OpenAPI)
2. **국내/외 기업:** 글로벌 프리랜서/B2B 플랫폼(Upwork 등), 글로벌 RFP 수집 사이트 (추후 확장)

**Outputs:**
- `event_data.js`: 수집된 입찰 정보를 FullCalendar 프론트엔드가 읽을 수 있는 JS 배열 형태로 저장

**Execution Scripts:**
- `execution/collect_koneps_bids.py`: 조달청(나라장터) OPEN API를 통해 리서치 관련 입찰정보 수집
- `execution/collect_global_rfps.py`: 글로벌 RFP 수집 (미구현)
- `execution/update_calendar_bids.py`: 오케스트레이터 — 수집 후 `event_data.js` 갱신 및 GitHub Pages 자동 배포

**Schedule:** 매주 월/수/금 (Windows Task Scheduler)

---

## API 상세 (나라장터 공공데이터개방표준서비스)

- **Endpoint:** `http://apis.data.go.kr/1230000/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo`
- **Portal:** https://www.data.go.kr/data/15058815/openapi.do
- **인증키:** `.env` 파일의 `KONEPS_API_KEY`

### 파라미터
| 파라미터 | 설명 | 비고 |
|---|---|---|
| `serviceKey` | API 인증키 | 필수 |
| `bidNtceBgnDt` | 공고일시 시작 (`YYYYMMDDHHMM`) | 필수 |
| `bidNtceEndDt` | 공고일시 종료 (`YYYYMMDDHHMM`) | 필수 |
| `bidNtceNm` | 공고명 키워드 검색 | 공식 미기재이나 실제 동작 확인됨 |
| `numOfRows` | 페이지당 건수 (최대 100) | |
| `pageNo` | 페이지 번호 | |
| `type` | 응답 형식 (`json`) | |

### ⚠️ 중요 제약사항
- **날짜 범위 제한:** API 허용 범위는 **약 30일** 이내. 초과 시 오류코드 `07` 반환.
  - 권장: `bidNtceBgnDt = today - 1일`, `bidNtceEndDt = today + 30일`
- **키워드당 최대 200건 제한 권장:** `'리서치'`처럼 광범위한 키워드는 수천 건 반환 → 무한 루프 방지
- **응답 구조:** `{"response": {"header": {"resultCode": "00"}, "body": {"items": [...], "totalCount": N}}}`
- **Rate Limit:** 키워드 간 0.5초, 페이지 간 0.3초 간격 유지

### 검색 키워드 목록
`시장조사`, `소비자조사`, `사용자조사`, `UX리서치`, `만족도조사`, `사회조사`, `패널조사`, `리서치`, `설문조사`

### 오류 코드
| 코드 | 의미 | 대응 |
|---|---|---|
| `00` | 성공 | |
| `07` | 입력값 범위 초과 | 날짜 범위 축소 |
| `10` | ServiceKey 없음 | `.env` 확인 |
| `11` | 필수 파라미터 누락 | 파라미터 확인 |
