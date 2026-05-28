"""
Google Drive Storage Backend for Django
"""
import os
from django.core.files.storage import Storage
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google.oauth2.service_account import Credentials
from django.conf import settings
import io


class GoogleDriveStorage(Storage):
    """
    Custom Django storage backend for Google Drive with Shared Drive support
    Supports organized folder structure by section, employee, and year.
    """
    
    def __init__(self, shared_drive_id=None, section=None):
        self.shared_drive_id = shared_drive_id or getattr(settings, 'GOOGLE_DRIVE_SHARED_DRIVE_ID', None)
        self.credentials_path = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_PATH', None)
        self.section = section  # e.g., 'Leave Requests', 'Work Assignments', 'Interventions'
        self.service = None
        self.folder_cache = {}  # Cache folder IDs to avoid repeated searches
        self.section_folder_id = None  # Cache the section folder ID
        
    def _get_employee_name(self, employee_id):
        """Get employee name from database by ID"""
        try:
            # Lazy import to avoid circular dependencies
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(id=employee_id).first()
            if user:
                # Return full name if available, otherwise username
                full_name = user.get_full_name()
                if full_name and full_name.strip():
                    return full_name.strip()
                return user.username
        except Exception as e:
            # If any error, return None (fallback to generic name)
            pass
        return None
    
    def _get_or_create_folder(self, folder_name, parent_id=None):
        """Get or create a folder in Google Drive - prevents duplicates"""
        service = self._get_service()
        
        # Create cache key
        cache_key = f"{parent_id or 'shared_drive'}:{folder_name}"
        
        # Check cache first
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]
        
        # Search for existing folder with same name in parent
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        if parent_id:
            # Search in specific parent folder
            results = service.files().list(
                q=query,
                corpora='drive',
                driveId=self.shared_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id, name, parents)'
            ).execute()
            
            # Filter by parent to find folder in correct location
            files = results.get('files', [])
            for file in files:
                if parent_id in file.get('parents', []):
                    folder_id = file['id']
                    self.folder_cache[cache_key] = folder_id
                    return folder_id
        else:
            # Search in shared drive root
            results = service.files().list(
                q=query,
                corpora='drive',
                driveId=self.shared_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                self.folder_cache[cache_key] = folder_id
                return folder_id
        
        # Folder not found, create it
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        # Set parent
        if parent_id:
            folder_metadata['parents'] = [parent_id]
        elif self.shared_drive_id:
            folder_metadata['parents'] = [self.shared_drive_id]
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        folder_id = folder.get('id')
        self.folder_cache[cache_key] = folder_id
        return folder_id
    
    def _create_folder_structure(self, path):
        """Create folder structure from path and return the final folder ID"""
        if not path:
            return self.shared_drive_id
        
        # Split path into components
        parts = path.strip('/').split('/')
        
        # Start from shared drive root
        current_parent = self.shared_drive_id
        
        # Create each folder in the path
        for part in parts:
            if not part:
                continue
            current_parent = self._get_or_create_folder(part, current_parent)
        
        return current_parent
    
    def _get_service(self):
        """Initialize Google Drive service"""
        if self.service is None:
            if self.credentials_path:
                credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            else:
                raise Exception("Google Drive credentials file not configured")
            
            self.service = build('drive', 'v3', credentials=credentials)
        return self.service
    
    def _save(self, name, content):
        """Save file to Google Drive with organized folder structure"""
        service = self._get_service()
        
        # Normalize path separators to forward slashes
        name = name.replace('\\', '/')
        
        # Extract directory path and filename
        if '/' in name:
            dir_path, filename = name.rsplit('/', 1)
        else:
            dir_path = None
            filename = name
        
        # Parse the path to extract section, employee, year info
        # Expected path format: section/employee_id/year/month/filename
        # or: leave_attachments/2_mhh/2026/04/leave_new.pdf
        path_parts = dir_path.split('/') if dir_path else []
        
        # Determine section folder name
        if self.section:
            section_name = self.section
        elif path_parts:
            # Use first part of path as section (e.g., 'leave_attachments' -> 'Leave Requests')
            section_key = path_parts[0].lower()
            section_mapping = {
                'leave_attachments': 'Leave Requests',
                'assignments': 'Work Assignments',
                'interventions': 'Interventions',
                'employee_documents': 'Employee Documents',
                'fleet': 'Fleet Documents',
                'warehouse': 'Warehouse Documents',
            }
            section_name = section_mapping.get(section_key, path_parts[0].replace('_', ' ').title())
        else:
            section_name = 'General Documents'
        
        # Extract employee info (second part of path)
        if len(path_parts) >= 2:
            employee_part = path_parts[1]
            # Extract employee ID (digits before any non-digit character)
            employee_id = ''.join(filter(str.isdigit, employee_part)) or '0'
            
            # Try to get employee name from database
            employee_name = self._get_employee_name(employee_id)
            if employee_name:
                employee_folder = f"{employee_name} - ID: {employee_id}"
            else:
                employee_folder = f"Employee - ID: {employee_id}"
        else:
            employee_id = '0'
            employee_folder = "General"
        
        # Create or get section folder
        section_folder_id = self._get_or_create_folder(section_name, self.shared_drive_id)
        
        # For Leave Requests section, use organized structure
        if section_name == 'Leave Requests':
            # Create employee folder with name and ID
            employee_folder_id = self._get_or_create_folder(employee_folder, section_folder_id)
            
            # Extract leave type from path (third part)
            leave_type_folder = 'Other Leave'
            if len(path_parts) >= 3:
                leave_type_code = path_parts[2].lower()
                # Map leave type codes to readable folder names
                leave_type_mapping = {
                    'annual': '1. Annual Leave',
                    'sick': '2. Sick Leave',
                    'casual': '3. Casual Leave',
                    'maternity': '4. Maternity Leave',
                    'paternity': '5. Paternity Leave',
                    'bereavement': '6. Bereavement Leave',
                    'unpaid': '7. Unpaid Leave',
                    'compassionate': '8. Compassionate Leave',
                    'study': '9. Study Leave',
                    'emergency': '10. Emergency Leave',
                    'half_day': '11. Half Day Leave',
                    'other': '12. Other Leave',
                }
                leave_type_folder = leave_type_mapping.get(leave_type_code, '12. Other Leave')
            
            # Create leave type folder inside employee folder
            leave_type_folder_id = self._get_or_create_folder(leave_type_folder, employee_folder_id)
            
            # Extract year from path (4-digit number)
            year_folder = None
            for part in path_parts:
                if part.isdigit() and len(part) == 4 and int(part) > 2000 and int(part) < 2100:
                    year_folder = part
                    break
            
            # Use current year if not found
            if not year_folder:
                from datetime import datetime
                year_folder = str(datetime.now().year)
            
            # Create year folder inside leave type folder
            year_folder_id = self._get_or_create_folder(year_folder, leave_type_folder_id)
            current_parent = year_folder_id
            
            # Update organized path for reference
            organized_path = f"{section_name}/{employee_folder}/{leave_type_folder}/{year_folder}/{filename}"
        
        # For Employee Documents section, use special organization
        elif section_name == 'Employee Documents':
            # Create employee folder with name and ID
            employee_folder_id = self._get_or_create_folder(employee_folder, section_folder_id)
            
            # Try to extract document type from path or detect from filename
            doc_type_folder = None
            
            # Check if any path part is a document type (not a year)
            for part in path_parts[2:] if len(path_parts) > 2 else []:
                if part.isdigit():
                    continue  # Skip numeric parts (year, month)
                # Check if this looks like a document type
                doc_type = part.lower()
                doc_type_mapping = {
                    # From EmployeeDocument model
                    'resume': '1. Resumes and CVs',
                    'contract': '2. Employment Contracts',
                    'id_proof': '3. ID Documents',
                    'address_proof': '4. Address Proof',
                    'education': '5. Education Certificates',
                    'experience': '6. Experience Certificates',
                    'passport': '7. Passport and Visa',
                    'visa': '7. Passport and Visa',
                    'medical': '8. Medical Certificates',
                    'police_verification': '9. Police Verification',
                    'salary_slip': '10. Salary Slips',
                    'offer_letter': '11. Offer Letters',
                    # Common variations
                    'cv': '1. Resumes and CVs',
                    'certificates': '5. Education Certificates',
                    'id': '3. ID Documents',
                }
                if doc_type in doc_type_mapping:
                    doc_type_folder = doc_type_mapping[doc_type]
                    break
            
            # If no doc type in path, try to detect from filename
            if not doc_type_folder:
                filename_lower = filename.lower()
                if any(word in filename_lower for word in ['cv', 'resume', 'curriculum']):
                    doc_type_folder = '1. Resumes and CVs'
                elif any(word in filename_lower for word in ['contract', 'agreement']):
                    doc_type_folder = '2. Employment Contracts'
                elif any(word in filename_lower for word in ['certificate', 'certification', 'degree', 'diploma']):
                    doc_type_folder = '5. Education Certificates'
                elif any(word in filename_lower for word in ['id', 'passport', 'license', 'identity']):
                    doc_type_folder = '3. ID Documents'
                elif any(word in filename_lower for word in ['photo', 'picture', 'image', 'portrait']):
                    doc_type_folder = 'Photos'
                else:
                    doc_type_folder = 'General Documents'
            
            # Create document type folder inside employee folder
            doc_type_folder_id = self._get_or_create_folder(doc_type_folder, employee_folder_id)
            
            # Extract year from path (4-digit number)
            year_folder = None
            for part in path_parts:
                if part.isdigit() and len(part) == 4 and int(part) > 2000 and int(part) < 2100:
                    year_folder = part
                    break
            
            # Use current year if not found
            if not year_folder:
                from datetime import datetime
                year_folder = str(datetime.now().year)
            
            # Create year folder inside document type folder
            year_folder_id = self._get_or_create_folder(year_folder, doc_type_folder_id)
            current_parent = year_folder_id
            
            # Update organized path for reference
            organized_path = f"{section_name}/{employee_folder}/{doc_type_folder}/{year_folder}/{filename}"
        
        # For other sections (default organization - Assignments, Interventions, etc.)
        else:
            # Create employee folder inside section
            employee_folder_id = self._get_or_create_folder(employee_folder, section_folder_id)
            
            # Extract year from path
            year_folder = None
            for part in path_parts:
                if part.isdigit() and len(part) == 4 and int(part) > 2000 and int(part) < 2100:
                    year_folder = part
                    break
            
            # Use current year if not found
            if not year_folder:
                from datetime import datetime
                year_folder = str(datetime.now().year)
            
            year_folder_id = self._get_or_create_folder(year_folder, employee_folder_id)
            current_parent = year_folder_id
            
            # Update organized path for reference
            organized_path = f"{section_name}/{employee_folder}/{year_folder}/{filename}"
        
        # Read file content
        file_metadata = {
            'name': filename
        }
        
        # Set parent to the organized folder structure
        file_metadata['parents'] = [current_parent]
        
        # Get content type
        content_type = getattr(content, 'content_type', 'application/octet-stream')
        
        # Read file content into memory for non-resumable upload
        content.seek(0)
        file_content = content.read()
        
        # Create media upload object (non-resumable for reliability)
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=content_type,
            resumable=False  # Use non-resumable to avoid timeout issues
        )
        
        # Upload file to shared drive
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        # Return the organized path for reference
        return organized_path
    
    def _open(self, name, mode='rb'):
        """Open file from Google Drive"""
        service = self._get_service()
        
        # Get file
        file = service.files().get(
            fileId=name, 
            fields='id, name',
            supportsAllDrives=True
        ).execute()
        
        # Download file content
        request = service.files().get_media(fileId=name, supportsAllDrives=True)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseUpload(file_handle, request)
        downloader.execute()
        file_handle.seek(0)
        
        return file_handle
    
    def delete(self, name):
        """Delete file from Google Drive"""
        service = self._get_service()
        service.files().delete(
            fileId=name,
            supportsAllDrives=True
        ).execute()
    
    def exists(self, name):
        """Check if file exists in Google Drive"""
        try:
            service = self._get_service()
            
            # Get the file name from the path
            file_name = name.split('/')[-1]
            
            # Search for the file by name
            query = f"name='{file_name}' and trashed=false"
            
            # If shared drive is configured, search within it
            if self.shared_drive_id:
                results = service.files().list(
                    q=query,
                    corpora='drive',
                    driveId=self.shared_drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields='files(id, name)'
                ).execute()
            else:
                results = service.files().list(
                    q=query,
                    fields='files(id, name)'
                ).execute()
            
            files = results.get('files', [])
            return len(files) > 0
        except:
            return False
    
    def url(self, name):
        """Get URL for file"""
        # Return a view URL that will serve the file
        return f'/media/google-drive/{name}/'
    
    def get_available_name(self, name, max_length=None):
        """Return a filename that's free in the storage"""
        return name
    
    def size(self, name):
        """Return file size"""
        service = self._get_service()
        
        # Get the file name from the path
        file_name = name.split('/')[-1]
        
        # Search for the file by name
        query = f"name='{file_name}' and trashed=false"
        
        # If shared drive is configured, search within it
        if self.shared_drive_id:
            results = service.files().list(
                q=query,
                corpora='drive',
                driveId=self.shared_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id, name, size)'
            ).execute()
        else:
            results = service.files().list(
                q=query,
                fields='files(id, name, size)'
            ).execute()
        
        files = results.get('files', [])
        
        if not files:
            return 0
        
        # Get the first matching file's size
        file = files[0]
        return int(file.get('size', 0))
