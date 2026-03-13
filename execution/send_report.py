import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_update_report(content, receiver="***REMOVED_EMAIL***"):
    sender_email = "***REMOVED_EMAIL***"
    app_password = "***REMOVED***"
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
