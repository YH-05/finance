import mimetypes
import os.path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# スコープを設定します。変更が必要な場合は、生成されたtoken.jsonを削除してください。
# スコープ: .fileから変更し、ファイルの作成・検索・フォルダ作成を許可
SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_folder_id_by_path(service, folder_path_list):
    """
    指定されたパスのリストをたどり、最終的なフォルダIDを返します。

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google Drive APIのサービスオブジェクト。
    folder_path_list : List[str]
        フォルダ名のリスト（パスの階層順）。

    Returns
    -------
    str
        最終的なフォルダのID。
    """
    parent_id = "root"

    for folder_name in folder_path_list:
        query = (
            f"name='{folder_name}' and '{parent_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and trashed=false"
        )

        response = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )
        files = response.get("files", [])

        if files:
            parent_id = files[0].get("id")
            print(f"フォルダ '{folder_name}' を見つけました (ID: {parent_id})")
        else:
            print(f"フォルダ '{folder_name}' が見つかりません。新規作成します。")
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = service.files().create(body=file_metadata, fields="id").execute()
            parent_id = folder.get("id")
            print(f"フォルダを作成しました (ID: {parent_id})")

    return parent_id


def upload_file_to_drive(local_file_paths: List[str], drive_folder_path_str: str):
    """
    ローカルファイルをGoogle Driveの指定フォルダパス（文字列）にアップロードします。

    Parameters
    ----------
    local_file_paths : List[str]
        アップロードするローカルファイルのパスのリスト。
    drive_folder_path_str : str
        Google Drive上のアップロード先フォルダパス（例: "MyFolder/SubFolder"）。

    Returns
    -------
    None
    """

    # --- 認証処理 (変更なし) ---
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        # ★変更点: 文字列パスを'/'で分割してリストに変換
        folder_path_list = drive_folder_path_str.split("/")

        # 1. パスをたどって格納先フォルダのIDを取得
        folder_id = get_folder_id_by_path(service, folder_path_list)
        if not folder_id:
            print("フォルダIDの取得に失敗したため、処理を中断します。")
            return

        for local_file_path in local_file_paths:
            if not os.path.exists(local_file_path):
                print(f"スキップ: ファイルが見つかりません - {local_file_path}")
                continue  # 次のファイルへ

            print(f"\nアップロード処理開始: {local_file_path}")

            # ファイルメタデータの設定
            file_name = os.path.basename(local_file_path)
            file_metadata = {"name": file_name, "parents": [folder_id]}

            # MIMEタイプを自動判別
            mimetype, _ = mimetypes.guess_type(local_file_path)
            if mimetype is None:
                mimetype = "application/octet-stream"

            media = MediaFileUpload(local_file_path, mimetype=mimetype, resumable=True)

            # ファイルをアップロード
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id, webViewLink")
                .execute()
            )

            print(f"  -> ✅ アップロード完了 (File ID: {file.get('id')})")

    except HttpError as error:
        print(f"An error occurred: {error}")
