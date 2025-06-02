import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

from app.utils import utils

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_youtube_service():
    """Get authenticated YouTube service."""
    creds = None
    token_file = os.path.join(utils.root_dir(), 'token.pickle')
    client_secrets_file = os.path.join(utils.root_dir(), 'client_secret.json')

    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                logger.error("client_secret.json not found, please put it in the project root directory")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            # add http://localhost:8090/ in Authorized redirect URIs of https://console.cloud.google.com/auth/clients
            creds = flow.run_local_server(port=8090)
            logger.info(f"Authentication successful")
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

def upload_video(video_file, title, description, privacy_status='private', tags=None):
    """
    Upload a video to YouTube.
    
    Args:
        video_file (str): Path to the video file
        title (str): Title of the video
        description (str): Description of the video
        privacy_status (str): Privacy status ('private', 'unlisted', or 'public')
        tags (list): List of tags for the video (optional)
    
    Returns:
        str: YouTube video ID if successful, None if failed
    """
    try:
        youtube = get_youtube_service()
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags if tags else [],
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                video_file, 
                chunksize=-1, 
                resumable=True
            )
        )

        logger.info(f"Starting upload of video: {title}")
        response = insert_request.execute()
        video_id = response.get('id')
        
        if video_id:
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            return video_id
        else:
            logger.error("Failed to get video ID from upload response")
            return None

    except Exception as e:
        logger.error(f"An error occurred during video upload: {str(e)}")
        return None
