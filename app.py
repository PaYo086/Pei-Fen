from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    # ApiClient,
    # MessagingApi,
    # ReplyMessageRequest,
    # TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    # TextMessageContent,
    # JoinEvent
)
import requests, datetime, dropbox, os
from dropbox.exceptions import ApiError

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

app = Flask(__name__)

# line
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(CHANNEL_SECRET)

# dropbox
dbx = dropbox.Dropbox(app_key=DROPBOX_APP_KEY, app_secret=DROPBOX_APP_SECRET, oauth2_refresh_token=DROPBOX_REFRESH_TOKEN)
base_path = "/timeinv/_個人/霈芬/"
folders = {"":"其他", "C68719ec0192673bf74f9683e5cb0ea12": "測試用", "Cb5afc0c051e0d90848393d03707b4d13": "永豐", "C180967dcc97bb4bea48b46b3bb91f8e1": "凱基momo", "C6ce749ed4f8989aaccdb5a1971e3fca9": "國泰", "C80d2e21fd4dd5a74eb6db60da1033ac6":"統一", "C68d4f9c8456b67910b84e52a7f7e651e":"元富", "C0e107f6f00fd97f9dd3721c07271699f":"元大", "C8bab64df80489c86d4cfa87a82c3f5f3":"華南永昌", "Ce49c6a6a6b14a969c18cfb91376b54d8":"凱基paggy", "C3300ddb838732cb9aaff3a6f429c9e4b":"中國信託", "C45ec95e0c64a04899d52979bd6748846":"福邦", "C225cadc134c5e76064ed4a681719bcc6":"宏遠", "C2e177dec40cb5c2bc4c1e064e5f06910":"康和", "C30611e72f285bc61236805461a3e9279":"IR Trust", "Cf749e2e1ea9988d8e1274d02fb702ceb":"兆豐"}

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@line_handler.add(MessageEvent)
def handle_message(event):
    message_type = event.message.type
    message_id = event.message.id
    message_date = datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d")
    group_id = event.source.group_id if event.source.type == "group" else ""
    path = base_path + folders.get(group_id, group_id) + "/"
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    res = requests.get(url, headers=headers)

    if message_type == "image":
        if res.status_code == 200:
            file_name = get_unique_filename(path + message_date, ".jpg")
            dbx.files_upload(res.content, file_name, mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
        else:
            metadata, dbx_res = dbx.files_download(base_path + "log.txt")
            log = dbx_res.content.decode("utf-8") + f"Image download failed\nTime: {datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d %H:%M:%S")}\nGroup ID: {group_id}\nStatus code: {res.status_code}\nResponse: {res.text}\n\n"
            dbx.files_upload(log.encode("utf-8"), base_path + "log.txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download failed", res.status_code, res.text)

    elif message_type == "video":
        if res.status_code == 200:
            file_name = get_unique_filename(path + message_date, ".mp4")
            dbx.files_upload(res.content, file_name, mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
        else:
            metadata, dbx_res = dbx.files_download(base_path + "log.txt")
            log = dbx_res.content.decode("utf-8") + f"Video download failed\nTime: {datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d %H:%M:%S")}\nGroup ID: {group_id}\nStatus code: {res.status_code}\nResponse: {res.text}\n\n"
            dbx.files_upload(log.encode("utf-8"), base_path + "log.txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download failed", res.status_code, res.text)

    elif message_type == "audio":
        if res.status_code == 200:
            file_name = get_unique_filename(path + message_date, ".m4a")
            dbx.files_upload(res.content, file_name, mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
        else:
            metadata, dbx_res = dbx.files_download(base_path + "log.txt")
            log = dbx_res.content.decode("utf-8") + f"Audio download failed\nTime: {datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d %H:%M:%S")}\nGroup ID: {group_id}\nStatus code: {res.status_code}\nResponse: {res.text}\n\n"
            dbx.files_upload(log.encode("utf-8"), base_path + "log.txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download failed", res.status_code, res.text)

    elif message_type == "file":
        if res.status_code == 200:
            file_name = path + event.message.file_name
            dbx.files_upload(res.content, file_name, mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
        else:
            metadata, dbx_res = dbx.files_download(base_path + "log.txt")
            log = dbx_res.content.decode("utf-8") + f"File download failed\nTime: {datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d %H:%M:%S")}\nGroup ID: {group_id}\nStatus code: {res.status_code}\nResponse: {res.text}\n\n"
            dbx.files_upload(log.encode("utf-8"), base_path + "log.txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download failed", res.status_code, res.text)

    elif message_type == "text":
        if file_exists(path + message_date + ".txt", dbx):
            metadata, dbx_res = dbx.files_download(path + message_date + ".txt")
            text = dbx_res.content.decode("utf-8") + event.message.text + "\n\n\n"
            dbx.files_upload(text.encode("utf-8"), path + message_date + ".txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
        else:
            text = event.message.text + "\n\n\n"
            dbx.files_upload(text.encode("utf-8"), path + message_date + ".txt", mode=dropbox.files.WriteMode('overwrite'))
            # print("Download completed")
    else:
        metadata, dbx_res = dbx.files_download(base_path + "log.txt")
        log = dbx_res.content.decode("utf-8") + f"Unsupported message type: {message_type}\nTime: {datetime.datetime.fromtimestamp(event.timestamp/1000).strftime("%Y%m%d %H:%M:%S")}\nGroup ID: {group_id}\n\n"
        dbx.files_upload(log.encode("utf-8"), base_path + "log.txt", mode=dropbox.files.WriteMode('overwrite'))

def get_unique_filename(base_name, ext, dbx=dbx):
    # base_name: without extension (can include path)
    i = 1
    file_name = f"{base_name}_{i:02d}{ext}"
    while file_exists(file_name, dbx):
        i += 1
        file_name = f"{base_name}_{i:02d}{ext}"
    return file_name

def file_exists(file_name, dbx=dbx):
    # file_name: path + filename
    try:
        dbx.files_get_metadata(file_name)
        return True
    except ApiError as e:
        if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path():
            return False
        raise

# @line_handler.add(JoinEvent)
# def handle_join(event):
#     if event.source.type == "group":
#         group_id = event.source.group_id
#         print("*"*20)
#         print(f"Joined Group ID: {group_id}")
#         print("*"*20)

if __name__ == "__main__":
    app.run()