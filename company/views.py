from django.http import HttpResponse, Http404
from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
import io
import logging

logger = logging.getLogger(__name__)


def serve_google_drive_file(request, file_path):
    """
    Serve a file from Google Drive by path.
    Supports both old flat structure and new organized folder structure.
    """
    # Get the file name from the path
    file_name = file_path.split('/')[-1]
    
    logger.info(f"Serving Google Drive file: path={file_path}, name={file_name}")
    
    # Get Google Drive service
    credentials_path = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_PATH', None)
    if not credentials_path:
        logger.error("Google Drive credentials not configured")
        raise Http404("Google Drive not configured")
    
    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    
    service = build('drive', 'v3', credentials=credentials)
    
    # Get shared drive ID
    shared_drive_id = getattr(settings, 'GOOGLE_DRIVE_SHARED_DRIVE_ID', None)
    logger.info(f"Shared drive ID: {shared_drive_id}")
    
    # Search for the file by name (works for both old and new folder structures)
    query = f"name='{file_name}' and trashed=false and mimeType!='application/vnd.google-apps.folder'"
    
    # If shared drive is configured, search within it
    if shared_drive_id:
        # Search in shared drive
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=shared_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name, mimeType, parents, size)'
        ).execute()
    else:
        # Search in all drives
        results = service.files().list(
            q=query,
            fields='files(id, name, mimeType, parents, size)'
        ).execute()
    
    files = results.get('files', [])
    
    logger.info(f"Found {len(files)} files matching '{file_name}'")
    
    if not files:
        logger.error(f"File not found: {file_name}")
        raise Http404(f"File not found: {file_name}")
    
    # If multiple files found, prefer the one in the organized structure
    # (has more parent folders indicating deeper nesting)
    if len(files) > 1:
        # Sort by number of parents (more parents = deeper in organized structure)
        files.sort(key=lambda f: len(f.get('parents', [])), reverse=True)
        logger.info(f"Multiple files found, selected one with most parent folders: {files[0]['name']}")
    
    # Get the first matching file
    file = files[0]
    file_id = file['id']
    mime_type = file.get('mimeType', 'application/octet-stream')
    
    logger.info(f"Downloading file: id={file_id}, name={file['name']}, mimeType={mime_type}")
    
    # Download file content
    try:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.info(f"Download progress: {int(status.progress() * 100)}%")
        
        file_handle.seek(0)
        file_content = file_handle.read()
        logger.info(f"Downloaded {len(file_content)} bytes")
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise Http404(f"Error downloading file: {e}")
    
    # Determine content type
    if 'image/jpeg' in mime_type or file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif 'image/png' in mime_type or file_name.lower().endswith('.png'):
        content_type = 'image/png'
    elif 'image/gif' in mime_type or file_name.lower().endswith('.gif'):
        content_type = 'image/gif'
    elif 'application/pdf' in mime_type or file_name.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream'
    
    # Return the file
    response = HttpResponse(file_content, content_type=content_type)
    
    # Set content disposition
    if 'image' in content_type or 'pdf' in content_type:
        # Display inline for images and PDFs
        response['Content-Disposition'] = f'inline; filename="{file_name}"'
    else:
        # Download for other files
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    
    return response
