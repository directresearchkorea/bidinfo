import os
import sys
import json
import logging
import traceback
import subprocess
from datetime import datetime

# Add current directory and parent to sys.path to easily import sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.collect_koneps_bids import fetch_bids_from_koneps, fetch_sejong_bids_from_koneps
from execution.collect_global_rfps import fetch_global_rfps

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
        else:
            logger.warning(f"Git Push 실패 또는 변경사항 없음: {push_res.stderr.strip()}")
            
    except Exception as e:
        logger.error(f"GitHub 배포 작업 중 오류 발생: {e}\n{traceback.format_exc()}")
        
    logger.info("모든 업데이트 작업이 완료되었습니다. Calendar를 확인하세요.")
