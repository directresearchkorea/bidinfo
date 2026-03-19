# 보안 지침 (Security Directive)

**목적:** GitHub 공개 저장소에 비밀번호·API 키 등 민감 정보가 노출되지 않도록 한다.

---

## 핵심 원칙

> **절대 코드(.py, .js 등)에 비밀번호, API 키, 토큰을 직접 작성하지 않는다.**

이 프로젝트는 **GitHub Pages**를 통해 웹사이트를 배포하고 있으며,
저장소가 **Public** 상태이므로 **모든 코드와 커밋 히스토리를 누구나 열람할 수 있다.**

---

## 필수 규칙

### 1. 민감 정보는 반드시 `.env`에 보관
```
# .env (git에 올라가지 않음)
GMAIL_USER=example@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
API_KEY=xxxxxxxx
```

### 2. 코드에서는 `os.environ.get()`으로 불러오기
```python
# ✅ 올바른 방식
from dotenv import load_dotenv
load_dotenv()
password = os.environ.get("GMAIL_APP_PASSWORD")

# ❌ 절대 금지
password = "실제비밀번호를여기적음"
```

### 3. `.gitignore` 철저 확인 및 검증
- **필수 포함 항목:**
  ```
  .env
  credentials.json
  token.json
  *.log
  ```
- **검증 방법:** 새로운 보안 관련 파일(설정 파일, 키 파일 등)을 생성할 때마다 **반드시 `.gitignore`에 해당 파일명이나 패턴이 포함되어 있는지 다시 한번 확인**한다.
- **Git 추적 상태 확인:** `git ls-files <파일명>` 명령어를 통해 해당 파일이 Git에 의해 추적되고 있지 않은지(결과가 비어있어야 함) 주기적으로 확인한다.

### 4. `git add .` 및 자동 배포 주의
자동 배포 스크립트(`update_calendar_bids.py`)가 `git add .`를 실행하므로, `.gitignore`에 등록되지 않은 모든 새 파일은 자동으로 GitHub에 업로드된다. 
- **새 파일 생성 시:** 코드를 작성하거나 파일을 추가할 때, 해당 파일에 민감한 정보가 포함되어 있다면 **반드시 `.gitignore` 설정을 먼저 완료**한 후에 작업을 진행한다.
- **커밋 전 확인:** `git status`를 통해 의도치 않은 민감 파일이 스테이징(`Changes to be committed`) 목록에 올라와 있지 않은지 확인하는 습관을 들인다.

---

## 사고 이력

| 날짜 | 내용 | 조치 |
|------|------|------|
| 2026-03-19 | Gmail 앱 비밀번호가 `send_report.py`에 하드코딩 → GitHub Public 저장소에 노출 | `.env` 방식으로 전환, `git filter-repo`로 히스토리 정리, force push 완료 |
