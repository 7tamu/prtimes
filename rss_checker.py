import requests
import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# **Google Sheets API の設定**
SHEET_ID = "1KzrFrE3EDxQLTYyXDtmG6GXtRabG4FV92HPoMcqeyAQ"
SHEET_NAME = "マスター"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# **Googleスプレッドシートに接続**
CREDENTIALS_FILE = "C:/Users/n/OneDrive/デスクトップ/credentials.json"
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# **スプレッドシートのデータ取得**
rows = sheet.get_all_values()[1:]  # ヘッダーを除外
rss_list = [(row[1], row[3], row[4]) for row in rows if row[3]]  # (企業名, RSS URL, 最終取得日時)

# **Slack Webhook設定**
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

# **RSSをチェックして新着があればSlack通知**
for company_name, rss_url, last_update in rss_list:
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print(f"⚠ {company_name} のRSSデータなし: {rss_url}")
        continue

    latest_entry = feed.entries[0]  # 最新の記事
    title = latest_entry.get("title", "タイトル不明")
    link = latest_entry.get("link", "リンクなし")
    pub_date = latest_entry.get("published", latest_entry.get("updated", "不明"))  # publishedがなければupdatedを使う

    # **過去の取得日時（E列の値）と比較**
    if pub_date != last_update:  # 新着があれば
        # **Slack通知**
        slack_message = f"📢 *{company_name}* の新着プレスリリース！\n📌 *{title}*\n🔗 {link}\n🕒 {pub_date}"
        requests.post(SLACK_WEBHOOK_URL, json={"text": slack_message})

        # **スプレッドシートの最終取得日時（E列）を更新**
        row_index = [row[1] for row in rows].index(company_name) + 2  # シートの行番号計算
        sheet.update_cell(row_index, 5, pub_date)

        print(f"✅ {company_name} の新着記事を通知しました: {title}")

print("🎯 RSSチェック完了")
