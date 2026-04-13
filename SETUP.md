# aBidInfo 프로젝트 재가동 및 설정 가이드 (RESTART GUIDE)

이 문서는 `aBidInfo` 프로젝트를 다른 컴퓨터로 복사했을 때, 정상적으로 작동시키기 위한 설정 및 실행 가이드를 제공합니다.

---

## 🏗️ 프로젝트 구조 (3-Layer Architecture)

본 프로젝트는 안정적인 운영을 위해 **3계층 구조**로 설계되었습니다:

1.  **Layer 1: Directives (`directives/`)**
    *   SOP(표준 운영 절차)가 포함된 마크다운 파일들입니다.
    *   무엇을 해야 하는지 정의하며, AI 모델(Antigravity)이 이를 읽고 판단합니다.
2.  **Layer 2: Orchestration**
    *   AI 모델인 Antigravity가 지시사항(Directives)을 읽고, 필요한 실행 스크립르를 호출하는 의사결정 단계입니다.
3.  **Layer 3: Execution (`execution/`)**
    *   실제 작업을 수행하는 결정론적인 파이썬 스크립트들입니다.
    *   환경 변수(`.env`)와 연동되어 API 호출, 데이터 수집, 파일 업데이트 등을 담당합니다.

---

## 🛠️ 사전 준비 사항 (Prerequisites)

새 컴퓨터에서 프로젝트를 실행하기 위해 다음 소프트웨어가 필요합니다:

1.  **Python 3.8+**: [python.org](https://www.python.org/)에서 설치 (설치 시 'Add Python to PATH' 옵션 필수 체크)
2.  **Git**: [git-scm.com](https://https://git-scm.com/)에서 설치 (GitHub 배포용)
3.  **Chrome 브라우저**: 데이터 스크래핑 및 대시보드 확인용.

---

## 🚀 설정 및 실행 순서

### 1. 프로젝트 복사 및 라이브러리 설치
프로젝트 폴더로 이동한 후, 터미널(PowerShell 또는 CMD)에서 필수 파이썬 라이브러리를 설치합니다.
```powershell
pip install -r requirements.txt
```

### 2. 환경 변수(`.env`) 설정
`.env` 파일은 프로젝트의 민감한 정보(API 키, 계정 등)를 담고 있으며, Git에 포함되지 않도록 설정되어 있습니다. (파일이 없다면 새로 만드세요.)

**[필수 항목]**
*   `KONEPS_API_KEY`: 조달청 나라장터 API 키 (이미 있는 경우 그대로 사용 가능)
*   `GMAIL_USER`: 알림을 보낼 Gmail 주소 (예: `your_id@gmail.com`)
*   `GMAIL_APP_PASSWORD`: Gmail의 **'앱 비밀번호'** (일반 비밀번호 대신 16자리 보안 코드)
    *   Google 계정 관리 > 보안 > 2단계 인증 > 앱 비밀번호에서 생성 가능합니다.

### 3. 데이터 수집 실행 (Scraper)
나라장터 등의 입찰 정보를 수집하고 대시보드 데이터를 업데이트하려면 `run_orchestrator.bat` 파일을 실행합니다.
*   **파일 위치**: 루트 폴더의 `run_orchestrator.bat`
*   **기능**: `execution/update_calendar_bids.py`를 실행하여 입찰 데이터를 수집하고 `event_data.js` 파일을 업데이트합니다.
*   **기록**: 실행 로그는 `collection_log.txt`에서 확인 가능합니다.

### 4. 대시보드 확인 및 배포
데이터 수집이 완료되면 `index.html`을 브라우저에서 열어 결과를 확인할 수 있습니다.

**GitHub Pages 배포 시:**
1.  `deploy_github.bat`를 실행하여 변경사항을 GitHub 리포지토리에 푸시합니다.
2.  GitHub Pages 설정이 되어 있다면 몇 분 후 웹상에서 대시보드가 업데이트됩니다.

---

## 🔧 주요 파일 설명

*   `AGENTS.md` / `GEMINI.md`: AI 가이드를 위한 아키텍처 규칙 파일
*   `execution/update_calendar_bids.py`: 입찰 정보를 수집하는 핵심 엔진
*   `event_data.js`: 수집된 입찰 데이터가 저장되는 JSON 변수 파일
*   `index.html` / `app.js`: 데이터 시각화 및 캘린더 인터페이스

---

## ⚠️ 주의사항

1.  **API 키 노출 금지**: `.env` 파일이나 API 키가 포함된 코드가 공용 GitHub 리포지토리에 커밋되지 않도록 주의하세요 (이미 `.gitignore`에 등록되어 있습니다).
2.  **날짜 형식**: `update_calendar_bids.py`는 현재 날짜를 기준으로 수집하므로, 컴퓨터의 시스템 날짜가 정확한지 확인하세요.
3.  **에러 해결**: `collection_log.txt`를 수시로 확인하여 스크래핑 과정에서 발생하는 차단이나 API 오류를 점검하세요.

---
**Direct Research Korea - Bid Intelligence System**
