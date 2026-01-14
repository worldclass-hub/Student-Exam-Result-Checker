# drive_service.py - UPDATED VERSION WITH .env SUPPORT
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
import re
from datetime import datetime
from dotenv import load_dotenv  # ADD THIS IMPORT

class GoogleDriveService:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()  # THIS LOADS YOUR .env FILE
        
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.service = self._authenticate()
        
        # MAIN "Emilia Report Card" FOLDER ID
        self.main_folder_id = "1S4UZEqGhCeBa-n3895jmSF22neTzCTZn"
        
        # Cache for folder IDs
        self.term_folders_cache = {}
        self.class_folders_cache = {}
        
        print("✅ Drive Service Ready - Emilia School Result System")
        print("🔐 Authentication: Using environment variables (.env)")
    
    def _authenticate(self):
        """Connect to Google Drive using environment variables"""
        # Get credentials JSON from environment variable
        creds_json = os.getenv('GOOGLE_CREDENTIALS')
        
        if not creds_json:
            raise Exception("❌ GOOGLE_CREDENTIALS not found in environment variables. Check your .env file")
        
        try:
            # Parse the JSON string from .env
            creds_dict = json.loads(creds_json)
            
            # Create credentials from the dictionary
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=self.SCOPES
            )
            
            print(f"✅ Authenticated as: {creds_dict.get('client_email')}")
            return build('drive', 'v3', credentials=credentials)
            
        except json.JSONDecodeError as e:
            raise Exception(f"❌ Invalid JSON in GOOGLE_CREDENTIALS: {str(e)}")
        except Exception as e:
            raise Exception(f"❌ Authentication failed: {str(e)}")
    
    # ============ ALL OTHER METHODS REMAIN EXACTLY THE SAME ============
    # (No changes needed to find_term_folder, find_class_folder, search_student_pdf, etc.)
    
    def find_term_folder(self, term_number, session):
        """
        Find term folder based on term number and session
        term_number: 1, 2, or 3
        session: '2025/2026', '2024/2025', etc.
        """
        cache_key = f"{term_number}-{session}"
        if cache_key in self.term_folders_cache:
            return self.term_folders_cache[cache_key]
        
        print(f"🔍 Looking for Term {term_number} {session} folder...")
        
        try:
            # List all folders in main directory
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=50
            ).execute()
            
            all_folders = results.get('files', [])
            
            if not all_folders:
                raise Exception(f"No term folders found in main directory")
            
            # Term mapping with variations
            term_mapping = {
                '1': {
                    'keywords': ['FIRST', '1ST', 'TERM 1', '1 TERM', 'TERM ONE'],
                    'priority': ['FIRST TERM', '1ST TERM', 'TERM 1']
                },
                '2': {
                    'keywords': ['SECOND', '2ND', 'TERM 2', '2 TERM', 'TERM TWO'],
                    'priority': ['SECOND TERM', '2ND TERM', 'TERM 2']
                },
                '3': {
                    'keywords': ['THIRD', '3RD', 'TERM 3', '3 TERM', 'TERM THREE'],
                    'priority': ['THIRD TERM', '3RD TERM', 'TERM 3']
                }
            }
            
            # Clean session for matching
            session_clean = session.upper().replace('/', ' ').replace('-', ' ')
            session_variations = [
                session_clean,
                session_clean.replace(' ', ''),
                session_clean.replace(' ', '/'),
                session_clean.replace(' ', '-')
            ]
            
            matching_folders = []
            
            # Find all folders that match session
            for folder in all_folders:
                folder_name_upper = folder['name'].upper()
                
                # Check if folder contains any session variation
                session_match = False
                for session_var in session_variations:
                    if session_var in folder_name_upper:
                        session_match = True
                        break
                
                if session_match:
                    matching_folders.append(folder)
            
            if not matching_folders:
                print("📋 Available folders in main directory:")
                for folder in all_folders:
                    print(f"   📁 {folder['name']}")
                raise Exception(f"No folders found for session {session}")
            
            # Now look for term match among session-matched folders
            term_keywords = term_mapping.get(str(term_number), {})
            term_priority = term_keywords.get('priority', [])
            term_keyword_list = term_keywords.get('keywords', [])
            
            # First try priority matches
            for priority_term in term_priority:
                for folder in matching_folders:
                    folder_name_upper = folder['name'].upper()
                    if priority_term in folder_name_upper:
                        print(f"✅ Found exact match: '{folder['name']}'")
                        self.term_folders_cache[cache_key] = folder['id']
                        return folder['id']
            
            # Then try any keyword match
            for keyword in term_keyword_list:
                for folder in matching_folders:
                    folder_name_upper = folder['name'].upper()
                    if keyword in folder_name_upper:
                        print(f"✅ Found keyword match: '{folder['name']}'")
                        self.term_folders_cache[cache_key] = folder['id']
                        return folder['id']
            
            # If still not found, show what we found
            print("📋 Session-matched folders:")
            for folder in matching_folders:
                print(f"   📁 {folder['name']}")
            
            raise Exception(f"Term {term_number} not found among session folders")
            
        except Exception as e:
            print(f"❌ Error finding term folder: {str(e)}")
            raise
    
    def find_class_folder(self, term_number, session, class_name):
        """Find class folder inside term folder"""
        cache_key = f"{term_number}-{session}-{class_name}"
        if cache_key in self.class_folders_cache:
            return self.class_folders_cache[cache_key]
        
        try:
            # First find the term folder
            term_folder_id = self.find_term_folder(term_number, session)
            
            print(f"🔍 Looking for {class_name} in Term {term_number} {session}...")
            
            # List all folders inside term folder
            query = f"'{term_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=50
            ).execute()
            
            class_folders = results.get('files', [])
            
            if not class_folders:
                # Try to find if there are nested folders (like "JSS 1 REPORT SHEET...")
                # Get all folders and files in term folder
                query_all = f"'{term_folder_id}' in parents and trashed=false"
                results_all = self.service.files().list(
                    q=query_all,
                    fields="files(id, name, mimeType)",
                    pageSize=100
                ).execute()
                
                all_items = results_all.get('files', [])
                print(f"📁 Found {len(all_items)} items in term folder")
                
                # Look for folders that might contain class name
                for item in all_items:
                    if item.get('mimeType') == 'application/vnd.google-apps.folder':
                        folder_name_upper = item['name'].upper()
                        class_upper = class_name.upper()
                        
                        # Try different matching strategies
                        if (class_upper in folder_name_upper or 
                            class_upper.replace(' ', '') in folder_name_upper.replace(' ', '') or
                            (class_name.startswith('JSS') and f"JSS {class_name[3:]}" in folder_name_upper) or
                            (class_name.startswith('SS') and f"SS {class_name[2:]}" in folder_name_upper)):
                            
                            print(f"✅ Found class folder (nested): '{item['name']}'")
                            self.class_folders_cache[cache_key] = item['id']
                            return item['id']
                
                # If we get here, show what we found
                print("📋 All folders in term directory:")
                folders_in_term = [item for item in all_items if item.get('mimeType') == 'application/vnd.google-apps.folder']
                for folder in folders_in_term:
                    print(f"   📁 {folder['name']}")
                
                raise Exception(f"No class folders found in Term {term_number}")
            
            # Look for class folder directly
            class_upper = class_name.upper()
            
            for folder in class_folders:
                folder_name_upper = folder['name'].upper()
                
                # Exact match
                if class_upper == folder_name_upper:
                    print(f"✅ Found class folder: '{folder['name']}'")
                    self.class_folders_cache[cache_key] = folder['id']
                    return folder['id']
                
                # Contains match
                if class_upper in folder_name_upper:
                    print(f"✅ Found class folder (contains): '{folder['name']}'")
                    self.class_folders_cache[cache_key] = folder['id']
                    return folder['id']
                
                # Try variations
                class_variations = [
                    class_upper,
                    class_upper.replace(' ', ''),
                    class_upper.replace('SS', 'S S'),
                    class_upper.replace('JSS', 'J S S'),
                    f"JSS {class_name[3:]}" if class_name.startswith('JSS') else None,
                    f"SS {class_name[2:]}" if class_name.startswith('SS') else None,
                    f"{class_name} REPORT",
                    f"REPORT {class_name}"
                ]
                
                for variation in class_variations:
                    if variation and variation in folder_name_upper:
                        print(f"✅ Found class folder (variation): '{folder['name']}'")
                        self.class_folders_cache[cache_key] = folder['id']
                        return folder['id']
            
            # Show available class folders
            print(f"📋 Available class folders in Term {term_number}:")
            for folder in class_folders:
                print(f"   📁 {folder['name']}")
            
            raise Exception(f"Class {class_name} not found in Term {term_number}")
            
        except Exception as e:
            print(f"❌ Error finding class folder: {str(e)}")
            raise
    
    def search_student_pdf(self, term_number, session, class_name, student_name):
        """Find student PDF with full path"""
        print(f"\n🔍 SEARCH: {student_name} | Class: {class_name} | Term: {term_number} | Session: {session}")
        
        try:
            # 1. Find class folder
            folder_id = self.find_class_folder(term_number, session, class_name)
            
            # 2. Search for PDFs
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, modifiedTime, webViewLink, webContentLink)",
                pageSize=200
            ).execute()
            
            all_pdfs = results.get('files', [])
            print(f"📄 Found {len(all_pdfs)} PDFs in {class_name} folder")
            
            if not all_pdfs:
                # Try searching in all files (including subfolders)
                return self._search_deep(term_number, session, class_name, student_name)
            
            # 3. Search for student
            student_upper = student_name.upper().strip()
            found_pdfs = []
            
            for pdf in all_pdfs:
                pdf_name = pdf['name'].upper()
                
                # Different search strategies
                search_strategies = [
                    # Exact match
                    lambda pn=pdf_name: student_upper in pn,
                    # Without PDF extension
                    lambda pn=pdf_name: student_upper in pn.replace('.PDF', ''),
                    # First name only
                    lambda pn=pdf_name: ' ' in student_upper and student_upper.split()[0] in pn,
                    # Last name only
                    lambda pn=pdf_name: ' ' in student_upper and student_upper.split()[-1] in pn,
                    # Remove special characters
                    lambda pn=pdf_name: student_upper.replace('.', '').replace(',', '') in pn,
                    # Split and check each part
                    lambda pn=pdf_name: any(part in pn for part in student_upper.split() if len(part) > 2)
                ]
                
                if any(strategy() for strategy in search_strategies):
                    found_pdfs.append(self._format_file_info(pdf))
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s)")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return []
    
    def _search_deep(self, term_number, session, class_name, student_name):
        """Search deeper if no PDFs in main class folder"""
        print(f"🔍 Deep search for {student_name} in {class_name}...")
        
        try:
            # Find term folder
            term_folder_id = self.find_term_folder(term_number, session)
            
            # Search for PDFs that might be in subfolders or have class name in filename
            student_upper = student_name.upper().strip()
            class_upper = class_name.upper()
            
            # Build search query
            query_parts = [
                f"'{term_folder_id}' in parents",
                "mimeType='application/pdf'",
                "trashed=false"
            ]
            
            query = ' and '.join(query_parts)
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, modifiedTime, webViewLink, webContentLink, parents)",
                pageSize=200
            ).execute()
            
            all_pdfs = results.get('files', [])
            print(f"📄 Found {len(all_pdfs)} PDFs in term folder")
            
            found_pdfs = []
            
            for pdf in all_pdfs:
                pdf_name_upper = pdf['name'].upper()
                
                # Check if PDF name contains class reference
                class_in_pdf = (class_upper in pdf_name_upper or 
                              class_upper.replace(' ', '') in pdf_name_upper.replace(' ', ''))
                
                # Check if PDF name contains student name
                student_in_pdf = (student_upper in pdf_name_upper or
                                any(part in pdf_name_upper for part in student_upper.split() if len(part) > 2))
                
                if class_in_pdf and student_in_pdf:
                    found_pdfs.append(self._format_file_info(pdf))
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s) in deep search")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Deep search error: {str(e)}")
            return []
    
    def get_available_sessions(self):
        """Get all available sessions from folder names PLUS generate future sessions"""
        try:
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(name)",
                pageSize=50
            ).execute()
            
            folders = results.get('files', [])
            sessions = set()
            
            # Extract sessions from folder names
            session_pattern = r'(?:20\d{2}[-/]20\d{2}|20\d{2})'
            
            for folder in folders:
                folder_name = folder['name']
                matches = re.findall(session_pattern, folder_name)
                
                for match in matches:
                    if '/' not in match and '-' not in match:
                        # Single year like "2025"
                        sessions.add(f"{match}/{int(match)+1}")
                    else:
                        # Already in format "2025/2026" or "2025-2026"
                        session = match.replace('-', '/')
                        sessions.add(session)
            
            # Convert to list
            session_list = list(sessions)
            
            # Get the most recent session year from existing folders
            if session_list:
                # Extract year from newest session (e.g., "2025/2026" -> 2025)
                newest_year = int(sorted(session_list, reverse=True)[0].split('/')[0])
            else:
                # If no sessions found, use current year
                newest_year = datetime.now().year
            
            # Generate future sessions (up to 10 years in the future)
            future_sessions = []
            for i in range(10):  # Next 10 years
                future_year = newest_year + i
                future_session = f"{future_year}/{future_year + 1}"
                future_sessions.append(future_session)
            
            # Combine found sessions with future sessions
            all_sessions = session_list + future_sessions
            
            # Remove duplicates and sort (newest first)
            unique_sessions = list(dict.fromkeys(all_sessions))
            
            # Custom sort: newest to oldest
            def session_sort_key(s):
                try:
                    return int(s.split('/')[0])
                except:
                    return 0
            
            sorted_sessions = sorted(unique_sessions, key=session_sort_key, reverse=True)
            
            # Filter out sessions older than 2025/2026
            filtered_sessions = []
            for session in sorted_sessions:
                try:
                    start_year = int(session.split('/')[0])
                    if start_year >= 2025:
                        filtered_sessions.append(session)
                except:
                    # Keep if we can't parse it
                    filtered_sessions.append(session)
            
            return filtered_sessions
            
        except Exception as e:
            print(f"❌ Error getting sessions: {str(e)}")
            # Return default future sessions if error
            current_year = datetime.now().year
            future_sessions = [f"{year}/{year+1}" for year in range(2025, 2035)]
            return future_sessions
    
    def _format_file_info(self, file_data):
        """Format file information"""
        if 'size' in file_data:
            file_data['size_formatted'] = self._format_size(file_data['size'])
        if 'modifiedTime' in file_data:
            file_data['modifiedTime'] = file_data['modifiedTime'][:10]
        
        # Ensure download link
        if 'webContentLink' not in file_data and 'id' in file_data:
            file_data['webContentLink'] = f"https://drive.google.com/uc?id={file_data['id']}&export=download"
        
        return file_data
    
    def _format_size(self, size_bytes):
        """Make file size readable"""
        if not size_bytes:
            return "0B"
        
        try:
            size_bytes = int(size_bytes)
        except:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"
    
    def get_file_info(self, file_id):
        """Get file details"""
        file = self.service.files().get(
            fileId=file_id,
            fields="id, name, size, webContentLink, mimeType"
        ).execute()
        
        if 'size' in file:
            file['size_formatted'] = self._format_size(file['size'])
        
        return file
    
    def list_all_classes(self):
        """List all available class folders"""
        try:
            # Get first available term folder
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=1
            ).execute()
            
            folders = results.get('files', [])
            if not folders:
                return []
            
            # Use first term folder
            term_folder_id = folders[0]['id']
            
            # List class folders in term folder
            query = f"'{term_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(name)",
                pageSize=20
            ).execute()
            
            class_folders = results.get('files', [])
            return [folder['name'] for folder in class_folders]
            
        except Exception as e:
            print(f"❌ Error listing classes: {str(e)}")
            return []
    
    def system_status(self):
        """Check system health"""
        try:
            # Test connection
            self.service.files().list(pageSize=1).execute()
            
            # Get main folder info
            main_folder = self.service.files().get(
                fileId=self.main_folder_id,
                fields="name"
            ).execute()
            
            # Get available sessions
            sessions = self.get_available_sessions()
            
            return {
                'status': '✅ ONLINE',
                'main_folder': main_folder.get('name', 'Unknown'),
                'available_sessions': len(sessions),
                'sessions_sample': sessions[:5],
                'message': 'System is fully operational'
            }
            
        except Exception as e:
            return {
                'status': '❌ OFFLINE',
                'error': str(e),
                'message': 'System connection failed'
            }

# Create global instance
drive_service = GoogleDriveService()

# Startup message
print("\n" + "="*70)
print("🏫 EMILIA SCHOOL RESULT SYSTEM - SECURE VERSION")
print("="*70)
print("🔐 Authentication: Environment Variables (.env)")
print(f"📁 Main folder ID: {drive_service.main_folder_id}")
print("📂 Structure: Main → Term/Session → Class → Student PDFs")
print("✅ Support: All terms (1st, 2nd, 3rd) and sessions (2025-2035+)")
print("✅ Classes: JSS1, JSS2, JSS3, SS1, SS2, SS3")
print("="*70)