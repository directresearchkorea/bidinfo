import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# .env 파일에서 GMAIL_USER, GMAIL_APP_PASSWORD 읽어오기
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip()

GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def send_update_report(content, receiver="[REDACTED_EMAIL]"):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("이메일 전송 실패: .env 파일에 GMAIL_USER 및 GMAIL_APP_PASSWORD를 설정해주세요.")
        return
    sender_email = GMAIL_USER
    app_password = GMAIL_APP_PASSWORD
    receiver_email = receiver

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "BidInfo 시스템 업데이트 완료 보고 및 결과 요약"

    body = f"""안녕하세요,

BidInfo 입찰/RFP 시스템의 업데이트 및 데이터 수집이 성공적으로 완료되었습니다.

[요약 내용]
{content}

감사합니다.
"""

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("이메일 발송 성공!")
    except Exception as e:
        print(f"이메일 발송 실패: {e}")

if __name__ == "__main__":
    import sys
    content = sys.argv[1] if len(sys.argv) > 1 else "업데이트가 완료되었습니다."
    send_update_report(content)
