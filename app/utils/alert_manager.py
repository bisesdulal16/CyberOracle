import os, requests, json

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_alert(findings: list):
    if not findings: 
        return
    payload = {"text": f"⚠️ DLP alert – sensitive data detected: {findings}"}
    if SLACK_WEBHOOK_URL:
        requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
    else:
        print(payload)
