# drive_service.py - STRICT ID MATCHING (ID appears anywhere in filename)
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
import re
from datetime import datetime
from dotenv import load_dotenv

class GoogleDriveService:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.service = self._authenticate()
        
        # MAIN "Emilia Report Card" FOLDER ID
        self.main_folder_id = "1S4UZEqGhCeBa-n3895jmSF22neTzCTZn"
        
        # Cache for folder IDs
        self.term_folders_cache = {}
        self.class_folders_cache = {}
        
        print("✅ Drive Service Ready - Emilia School Result System")
        print("🔐 Authentication: Using environment variables (.env)")
        print("🔑 Student ID Verification: ID MUST APPEAR IN FILENAME")
        print("📊 Student ID Format: EMFHS-YYYY-XXX-XX (17 characters total)")
        print("🔍 Search Mode: ID must be present in filename (partial match allowed within filename)")
        print("⚠️  Year Matching: DISABLED - Search any session regardless of ID year")
    
    def _authenticate(self):
        """Connect to Google Drive using environment variables"""
        creds_json = os.getenv('GOOGLE_CREDENTIALS')
        
        if not creds_json:
            raise Exception("❌ GOOGLE_CREDENTIALS not found in environment variables. Check your .env file")
        
        try:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=self.SCOPES
            )
            print(f"✅ Authenticated as: {creds_dict.get('client_email')}")
            return build('drive', 'v3', credentials=credentials)
        except json.JSONDecodeError as e:
            raise Exception(f"❌ Invalid JSON in GOOGLE_CREDENTIALS: {str(e)}")
        except Exception as e:
            raise Exception(f"❌ Authentication failed: {str(e)}")
    
    def find_term_folder(self, term_number, session):
        """Find term folder based on term number and session"""
        cache_key = f"{term_number}-{session}"
        if cache_key in self.term_folders_cache:
            return self.term_folders_cache[cache_key]
        
        print(f"🔍 Looking for Term {term_number} {session} folder...")
        
        try:
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=50
            ).execute()
            
            all_folders = results.get('files', [])
            
            if not all_folders:
                raise Exception(f"No term folders found in main directory")
            
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
            
            session_clean = session.upper().replace('/', ' ').replace('-', ' ')
            session_variations = [
                session_clean,
                session_clean.replace(' ', ''),
                session_clean.replace(' ', '/'),
                session_clean.replace(' ', '-')
            ]
            
            matching_folders = []
            for folder in all_folders:
                folder_name_upper = folder['name'].upper()
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
            
            term_keywords = term_mapping.get(str(term_number), {})
            term_priority = term_keywords.get('priority', [])
            term_keyword_list = term_keywords.get('keywords', [])
            
            for priority_term in term_priority:
                for folder in matching_folders:
                    folder_name_upper = folder['name'].upper()
                    if priority_term in folder_name_upper:
                        print(f"✅ Found exact match: '{folder['name']}'")
                        self.term_folders_cache[cache_key] = folder['id']
                        return folder['id']
            
            for keyword in term_keyword_list:
                for folder in matching_folders:
                    folder_name_upper = folder['name'].upper()
                    if keyword in folder_name_upper:
                        print(f"✅ Found keyword match: '{folder['name']}'")
                        self.term_folders_cache[cache_key] = folder['id']
                        return folder['id']
            
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
            term_folder_id = self.find_term_folder(term_number, session)
            print(f"🔍 Looking for {class_name} in Term {term_number} {session}...")
            
            query = f"'{term_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=50
            ).execute()
            
            class_folders = results.get('files', [])
            
            if not class_folders:
                query_all = f"'{term_folder_id}' in parents and trashed=false"
                results_all = self.service.files().list(
                    q=query_all,
                    fields="files(id, name, mimeType)",
                    pageSize=100
                ).execute()
                all_items = results_all.get('files', [])
                print(f"📁 Found {len(all_items)} items in term folder")
                
                for item in all_items:
                    if item.get('mimeType') == 'application/vnd.google-apps.folder':
                        folder_name_upper = item['name'].upper()
                        class_upper = class_name.upper()
                        
                        if (class_upper in folder_name_upper or 
                            class_upper.replace(' ', '') in folder_name_upper.replace(' ', '') or
                            (class_name.startswith('JSS') and f"JSS {class_name[3:]}" in folder_name_upper) or
                            (class_name.startswith('SS') and f"SS {class_name[2:]}" in folder_name_upper)):
                            print(f"✅ Found class folder (nested): '{item['name']}'")
                            self.class_folders_cache[cache_key] = item['id']
                            return item['id']
                
                print("📋 All folders in term directory:")
                folders_in_term = [item for item in all_items if item.get('mimeType') == 'application/vnd.google-apps.folder']
                for folder in folders_in_term:
                    print(f"   📁 {folder['name']}")
                raise Exception(f"No class folders found in Term {term_number}")
            
            class_upper = class_name.upper()
            for folder in class_folders:
                folder_name_upper = folder['name'].upper()
                
                if class_upper == folder_name_upper:
                    print(f"✅ Found class folder: '{folder['name']}'")
                    self.class_folders_cache[cache_key] = folder['id']
                    return folder['id']
                
                if class_upper in folder_name_upper:
                    print(f"✅ Found class folder (contains): '{folder['name']}'")
                    self.class_folders_cache[cache_key] = folder['id']
                    return folder['id']
                
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
            
            print(f"📋 Available class folders in Term {term_number}:")
            for folder in class_folders:
                print(f"   📁 {folder['name']}")
            raise Exception(f"Class {class_name} not found in Term {term_number}")
        except Exception as e:
            print(f"❌ Error finding class folder: {str(e)}")
            raise
    
    def search_student_pdf(self, term_number, session, class_name, student_name, student_id=None):
        """
        Find student PDF - ID must appear in filename
        """
        print(f"\n🔍 SEARCHING FOR STUDENT RESULT:")
        print(f"   🔑 ID: {student_id}")
        print(f"   🏫 Class: {class_name}")
        print(f"   📅 Term: {term_number} | Session: {session}")
        
        if not student_id or student_id.strip() == '':
            print("❌ Student ID is required for search")
            return []
        
        try:
            folder_id = self.find_class_folder(term_number, session, class_name)
            
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, modifiedTime, webViewLink, webContentLink)",
                pageSize=200
            ).execute()
            
            all_pdfs = results.get('files', [])
            print(f"📄 Found {len(all_pdfs)} PDFs in {class_name} folder")
            
            # DEBUG: Print sample filenames
            print("📋 Sample PDF filenames in this folder:")
            for i, pdf in enumerate(all_pdfs[:10]):
                print(f"   {i+1}. {pdf['name']}")
            
            if not all_pdfs:
                return self._search_deep_with_id_match(term_number, session, class_name, student_id)
            
            student_id_upper = student_id.upper().strip()
            found_pdfs = []
            
            for pdf in all_pdfs:
                pdf_name = pdf['name'].upper()
                pdf_name_without_ext = pdf_name.replace('.PDF', '').replace('.PDF', '')
                
                # Check if the student ID appears ANYWHERE in the filename
                if student_id_upper in pdf_name_without_ext:
                    print(f"✅ ID FOUND IN FILENAME: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s)")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return []
    
    def _search_deep_with_id_match(self, term_number, session, class_name, student_id):
        """Deep search - ID must appear in filename"""
        print(f"🔍 Deep search for ID: {student_id}...")
        
        try:
            term_folder_id = self.find_term_folder(term_number, session)
            student_id_upper = student_id.upper().strip()
            
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
                pdf_name = pdf['name'].upper()
                pdf_name_without_ext = pdf_name.replace('.PDF', '').replace('.PDF', '')
                
                if student_id_upper in pdf_name_without_ext:
                    print(f"✅ DEEP SEARCH ID FOUND: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s) in deep search")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Deep search error: {str(e)}")
            return []
    
    def _extract_year_from_id(self, student_id):
        """Extract year from student ID (FOR INFORMATION ONLY)"""
        patterns = [
            r'EMFHS-(\d{4})-[A-Z0-9]{3}-[A-Z0-9]{2}',
            r'EMFHS-(\d{4})-\d{3}-[A-Z0-9]{2}',
            r'EMFHS-(\d{4})-[A-Z0-9]{3}',
            r'EMFHS-(\d{4})-\d{3}',
            r'(\d{4})-[A-Z0-9]{3}-[A-Z0-9]{2}',
            r'(\d{4})-\d{3}-[A-Z0-9]{2}',
            r'(\d{4})-[A-Z0-9]{3}',
            r'(\d{4})-\d{3}',
        ]
        
        student_id_str = str(student_id).upper()
        for pattern in patterns:
            match = re.search(pattern, student_id_str)
            if match:
                try:
                    year = int(match.group(1))
                    return year
                except:
                    continue
        
        year_match = re.search(r'\b(20\d{2})\b', student_id_str)
        if year_match:
            try:
                year = int(year_match.group(1))
                return year
            except:
                pass
        return None
    
    def _extract_year_from_session(self, session):
        """Extract start year from session string"""
        try:
            parts = session.replace('/', '-').split('-')
            if parts and len(parts) > 0:
                return int(parts[0])
        except:
            pass
        match = re.search(r'\b(20\d{2})\b', session)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        return None
    
    def _format_file_info(self, file_data):
        """Format file information"""
        if 'size' in file_data:
            file_data['size_formatted'] = self._format_size(file_data['size'])
        if 'modifiedTime' in file_data:
            file_data['modifiedTime'] = file_data['modifiedTime'][:10]
        
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
    
    def get_available_sessions(self):
        """Get all available sessions from folder names"""
        try:
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(name)",
                pageSize=50
            ).execute()
            
            folders = results.get('files', [])
            sessions = set()
            session_pattern = r'(?:20\d{2}[-/]20\d{2}|20\d{2})'
            
            for folder in folders:
                folder_name = folder['name']
                matches = re.findall(session_pattern, folder_name)
                for match in matches:
                    if '/' not in match and '-' not in match:
                        sessions.add(f"{match}/{int(match)+1}")
                    else:
                        session = match.replace('-', '/')
                        sessions.add(session)
            
            session_list = list(sessions)
            
            if session_list:
                newest_year = int(sorted(session_list, reverse=True)[0].split('/')[0])
            else:
                newest_year = datetime.now().year
            
            future_sessions = []
            for i in range(10):
                future_year = newest_year + i
                future_session = f"{future_year}/{future_year + 1}"
                future_sessions.append(future_session)
            
            all_sessions = session_list + future_sessions
            unique_sessions = list(dict.fromkeys(all_sessions))
            
            def session_sort_key(s):
                try:
                    return int(s.split('/')[0])
                except:
                    return 0
            
            sorted_sessions = sorted(unique_sessions, key=session_sort_key, reverse=True)
            return sorted_sessions
            
        except Exception as e:
            print(f"❌ Error getting sessions: {str(e)}")
            current_year = datetime.now().year
            future_sessions = [f"{year}/{year+1}" for year in range(2000, current_year + 11)]
            return future_sessions
    
    def system_status(self):
        """System health check"""
        try:
            self.service.about().get(fields='user').execute()
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query, pageSize=1).execute()
            
            return {
                'status': '✅ SYSTEM READY',
                'main_folder': 'Connected',
                'authentication': 'Active',
                'total_folders': len(results.get('files', [])),
                'strict_id_matching': 'ENABLED - ID MUST APPEAR IN FILENAME',
                'student_name_verification': 'DISABLED',
                'year_restrictions': 'COMPLETELY DISABLED',
                'id_formats': 'EMFHS-YYYY-XXX-XX (17 characters)',
                'note': 'ID must appear in filename - search any session'
            }
        except Exception as e:
            return {
                'status': '❌ SYSTEM ERROR',
                'error': str(e),
                'strict_id_matching': 'ENABLED - ID MUST APPEAR IN FILENAME',
                'student_name_verification': 'DISABLED',
                'year_restrictions': 'COMPLETELY DISABLED',
                'id_formats': 'EMFHS-YYYY-XXX-XX (17 characters)'
            }
    
    def get_file_info(self, file_id):
        """Get file information"""
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, size, modifiedTime, webViewLink, webContentLink"
            ).execute()
            return self._format_file_info(file_info)
        except Exception as e:
            print(f"❌ Error getting file info: {str(e)}")
            return None

# Create global instance
drive_service = GoogleDriveService()

print("\n" + "="*70)
print("🏫 EMILIA SCHOOL RESULT SYSTEM - ID MUST APPEAR IN FILENAME")
print("="*70)
print("🔐 Authentication: Environment Variables (.env)")
print("🔑 Security: ID must appear anywhere in filename")
print("🆕 ID FORMAT: EMFHS-YYYY-XXX-XX (17 characters total)")
print("📝 Example: EMFHS-2025-VWW-UV")
print("❌ Student Name Verification: DISABLED")
print("❌ Year Restrictions: COMPLETELY DISABLED")
print("📁 Main folder ID: 1S4UZEqGhCeBa-n3895jmSF22neTzCTZn")
print("🔍 Search Mode: ID must be present in filename")
print("✅ Support: All terms (1st, 2nd, 3rd) and sessions (2000-2035+)")
print("✅ Classes: JSS1, JSS2, JSS3, SS1, SS2, SS3")
print("="*70)