import os
import sys
import json
import logging
import traceback
import subprocess
from datetime import datetime

# .env 로드 — collect 스크립트 import 전에 미리 환경변수 설정
from dotenv import load_dotenv
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))

# sys.path 설정 — execution 패키지 import 가능하도록
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_root)


from execution.collect_koneps_bids import fetch_bids_from_koneps, fetch_sejong_bids_from_koneps
from execution.collect_global_rfps import fetch_global_rfps
from execution.send_report import send_update_report

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - ORCHESTRATOR - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_event_data_js(merged_data):
    """
    수집된 입찰 데이터 리스트를 event_data.js 파일의 JS 변수로 저장합니다.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_file = os.path.join(project_root, 'event_data.js')
    
    try:
        json_data = json.dumps(merged_data, ensure_ascii=False, indent=4)
        js_content = f"// 자동 업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        js_content += f"const bidEvents = {json_data};\n"
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        logger.info(f"성공적으로 {len(merged_data)}개의 항목을 {target_file} 에 저장했습니다.")
    except Exception as e:
        logger.error(f"event_data.js 작성 중 오류 발생: {e}")

if __name__ == "__main__":
    from datetime import datetime
    
    logger.info("입찰/RFP 정보 자동 수집 사이클을 시작합니다.")
    all_bids = []
    
    # 1. 나라장터 스크래핑
    try:
        koneps_bids = fetch_bids_from_koneps()
        logger.info(f"나라장터 입찰 정보 {len(koneps_bids)}건을 수집했습니다.")
        all_bids.extend(koneps_bids)
    except Exception as e:
        logger.error(f"나라장터 수집 실패: {e}\n{traceback.format_exc()}")
        
    # 2. 세종시 산하기관 조달청 지정 스크래핑
    try:
        sejong_bids = fetch_sejong_bids_from_koneps()
        logger.info(f"세종 산하기관 지정 입찰 정보 {len(sejong_bids)}건을 수집했습니다.")
        all_bids.extend(sejong_bids)
    except Exception as e:
        logger.error(f"세종 산하기관 수집 실패: {e}\n{traceback.format_exc()}")
        
    # 3. 글로벌 RFP 스크래핑
    try:
        global_bids = fetch_global_rfps()
        logger.info(f"글로벌 입찰/RFP 정보 {len(global_bids)}건을 수집했습니다.")
        all_bids.extend(global_bids)
    except Exception as e:
        logger.error(f"글로벌 RFP 수집 실패: {e}\n{traceback.format_exc()}")
        
    # 3. 데이터 병합 및 UI 업데이트
    update_event_data_js(all_bids)
    
    # 4. 자동 Git 커밋 및 GitHub 배포
    logger.info("GitHub Pages 자동 배포(Push)를 시작합니다...")
    push_status = "확인되지 않음"
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Add files
        subprocess.run(["git", "add", "."], cwd=project_root, check=True, capture_output=True)
        
        # Commit changes (if no changes, commit will return non-zero exit code, so we don't strict check it here)
        commit_msg = f"Auto-deploy update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root)
        
        # Push to remote branch
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=project_root, capture_output=True, text=True)
        if push_res.returncode == 0:
            logger.info("GitHub 원격 저장소에 성공적으로 푸시(배포) 되었습니다. (약 1분 뒤 웹사이트 적용)")
            push_status = "성공 (배포 완료)"
        else:
            logger.warning(f"Git Push 실패 또는 변경사항 없음: {push_res.stderr.strip()}")
            push_status = "변경사항 없음 또는 실패"
            
    except Exception as e:
        logger.error(f"GitHub 배포 작업 중 오류 발생: {e}\n{traceback.format_exc()}")
        push_status = f"오류 발생: {e}"
        
    logger.info("모든 업데이트 작업이 완료되었습니다. Calendar를 확인하세요.")
    
    # 5. 결과 알림 이메일 전송
    report_content = f"""[업데이트 결과 요약]
- 나라장터 (일반): {len(koneps_bids) if 'koneps_bids' in locals() else 0}건
- 나라장터 (세종시): {len(sejong_bids) if 'sejong_bids' in locals() else 0}건
- 글로벌 RFP: {len(global_bids) if 'global_bids' in locals() else 0}건
---------------------------------------------------
총합계: {len(all_bids)}건 업데이트 됨

[배포 상태]
{push_status}

업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    try:
        send_update_report(report_content, receiver="***REMOVED_EMAIL***")
        logger.info("업데이트 결과 보고 이메일이 전송되었습니다.")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
