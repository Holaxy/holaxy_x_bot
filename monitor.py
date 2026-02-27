import os
import requests
import xml.etree.ElementTree as ET

# 從 GitHub Secrets 取得 Token 與 Chat ID
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ----- 這裡設定你想監控的看板與關鍵字 -----
TARGETS = {
    'Lifeismoney': ['情報', '特價', '情報'],
    'Gossiping': ['新聞', '問卦']
}
HISTORY_FILE = 'history.txt'

def send_telegram_notify(msg):
    # 加上詳細的 Log 輸出，方便我們在 Actions 裡看報錯原因
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 錯誤：找不到 TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID 環境變數！")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    
    print(f"準備發送訊息至 Chat ID: {TELEGRAM_CHAT_ID}")
    try:
        response = requests.post(url, json=payload)
        # 印出 Telegram 伺服器的完整回應
        print(f"Telegram API 回應碼: {response.status_code}")
        print(f"Telegram API 回應內容: {response.text}")
    except Exception as e:
        print(f"請求 Telegram 失敗: {e}")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines())

def save_history(history_set):
    recent_history = list(history_set)[-100:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(recent_history))

def main():
    history = load_history()
    new_notifies = 0

    for board, keywords in TARGETS.items():
        print(f"\n正在檢查 {board} 板...")
        url = f'https://www.ptt.cc/atom/{board}.xml'
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            
            root = ET.fromstring(res.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text
                link = entry.find('atom:id', ns).text
                
                if link not in history and any(k.lower() in title.lower() for k in keywords):
                    msg = f"🎯 <b>發現關鍵字！</b>\n\n看板: {board}\n標題: {title}\n連結: {link}"
                    send_telegram_notify(msg)
                    history.add(link)
                    new_notifies += 1
                    print(f"已排程通知: {title}")
                    
        except Exception as e:
            print(f"抓取 {board} 發生錯誤: {e}")

    if new_notifies > 0:
        save_history(history)
    else:
        print("沒有發現新文章。")

if __name__ == "__main__":
    main()
