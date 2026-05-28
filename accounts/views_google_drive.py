"""
View to serve files from Google Drive
"""
from django.http import HttpResponse, Http404
from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


def serve_google_drive_file(request, file_id):
    """
    Serve a file from Google Drive by its file ID
    """
    try:
        # Initialize Google Drive service
        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_DRIVE_CREDENTIALS_PATH,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # Get file metadata
        file_metadata = service.files().get(
            fileId=file_id,
            fields='name, mimeType'
        ).execute()
        
        # Download file content
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        # Create response with appropriate content type
        response = HttpResponse(
            file_content,
            content_type=file_metadata.get('mimeType', 'application/octet-stream')
        )
        
        # Set content disposition for download
        response['Content-Disposition'] = f'inline; filename="{file_metadata.get("name", "file")}"'
        
        return response
        
    except Exception as e:
        raise Http404(f"File not found or error accessing file: {str(e)}")
