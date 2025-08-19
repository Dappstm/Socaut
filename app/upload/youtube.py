import os, time
from typing import List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_service():
    client_secrets = os.getenv("YOUTUBE_CLIENT_SECRETS")
    token_file = os.getenv("YOUTUBE_TOKEN", "secrets/youtube-oauth-token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def upload_video(file_path: str, title: str, description: str, tags: List[str], categoryId: str = "22", privacyStatus: str = "public"):
    youtube = get_service()

    body=dict(
        snippet=dict(
            title=title,
            description=description,
            tags=tags,
            categoryId=categoryId
        ),
        status=dict(
            privacyStatus=privacyStatus,
            selfDeclaredMadeForKids=False
        )
    )

    # 9:16 + < 60s will be auto-considered Shorts by YouTube
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    print("Upload complete:", response.get("id"))
    return response
