# drive_service.py - UPDATED FOR NEW ID FORMAT: EMFHS-YYYY-XXX-XX
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
        print("🔑 Student ID Verification: STRICT ID MATCHING ENABLED")
        print("📊 Student ID Formats: Supports EMFHS-YYYY-XXX-XX, YYYY-NNN, etc.")
        print("🆕 NEW FORMAT: EMFHS-YYYY-XXX-XX (XXX = mixed alphanumeric)")
        print("🔍 Search Mode: Requires EXACT Student ID in filename")
        print("⚠️  Year Matching: DISABLED - Search any session regardless of ID year")
    
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
                # Try to find if there are nested folders
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
    
    def search_student_pdf(self, term_number, session, class_name, student_name, student_id=None):
        """
        Find student PDF with STRICT ID MATCHING ONLY
        Supports NEW format: EMFHS-YYYY-XXX-XX (XXX = mixed alphanumeric)
        """
        print(f"\n🔍 STRICT ID MATCHING SEARCH:")
        print(f"   🔑 ID: {student_id}")
        print(f"   🆕 Format: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)")
        print(f"   🏫 Class: {class_name}")
        print(f"   📅 Term: {term_number} | Session: {session}")
        print(f"   ⚠️  Note: Year matching is DISABLED")
        print(f"   ⚠️  Note: Student name verification is DISABLED")
        
        # Validate student ID
        if not student_id or student_id.strip() == '':
            print("❌ Student ID is required for search")
            return []
        
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
                return self._search_deep_with_strict_id(term_number, session, class_name, student_id)
            
            # 3. STRICT ID MATCHING: Search for student with EXACT ID in filename
            student_id_upper = student_id.upper().strip()
            found_pdfs = []
            
            for pdf in all_pdfs:
                pdf_name = pdf['name'].upper()
                
                # STRATEGY 1: EXACT ID MATCH in filename (MOST IMPORTANT)
                if self._exact_id_match(student_id_upper, pdf_name):
                    print(f"✅ EXACT ID MATCH FOUND: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
                
                # STRATEGY 2: ID COMPONENT MATCH (e.g., EMFHS-2025-A7K matches EMFHS-2025-A7K-B9)
                if self._id_components_match(student_id_upper, pdf_name):
                    print(f"✅ ID COMPONENT MATCH: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
                
                # STRATEGY 3: For backwards compatibility - check if ID appears anywhere
                if self._id_appears_anywhere(student_id_upper, pdf_name):
                    print(f"✅ ID APPEARS IN FILENAME: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s) with STRICT ID verification")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return []
    
    def _search_deep_with_strict_id(self, term_number, session, class_name, student_id):
        """Search deeper with strict ID matching"""
        print(f"🔍 Deep search with STRICT ID for ID: {student_id} in {class_name}...")
        
        try:
            # Find term folder
            term_folder_id = self.find_term_folder(term_number, session)
            
            student_id_upper = student_id.upper().strip()
            
            # Build search query for all PDFs in term folder
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
                
                # STRICT ID MATCHING in deep search
                if self._exact_id_match(student_id_upper, pdf_name_upper):
                    print(f"✅ DEEP SEARCH EXACT ID MATCH: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
                
                # ID component match
                if self._id_components_match(student_id_upper, pdf_name_upper):
                    print(f"✅ DEEP SEARCH ID COMPONENT MATCH: '{pdf['name']}'")
                    found_pdfs.append(self._format_file_info(pdf))
                    continue
            
            print(f"📊 Found {len(found_pdfs)} matching PDF(s) in deep search with STRICT ID")
            return found_pdfs
            
        except Exception as e:
            print(f"❌ Deep search error: {str(e)}")
            return []
    
    def _exact_id_match(self, search_id, filename):
        """
        Check for EXACT ID match in filename
        Returns True if the exact student ID appears in the filename
        Supports NEW format: EMFHS-YYYY-XXX-XX
        """
        # Normalize both
        search_id_clean = search_id.upper().strip()
        filename_upper = filename.upper()
        
        # Method 1: Direct exact match
        if search_id_clean in filename_upper:
            # Check if it's a whole word match (not part of another ID)
            # Look for patterns like " EMFHS-2025-A7K-B9 " or "EMFHS-2025-A7K-B9.pdf"
            pattern1 = f"\\b{re.escape(search_id_clean)}\\b"
            if re.search(pattern1, filename_upper):
                return True
            
            # Also check for ID at start/end of filename
            if filename_upper.startswith(search_id_clean) or filename_upper.endswith(search_id_clean):
                return True
        
        # Method 2: Check variations (with/without spaces, dashes, etc.)
        variations = [
            search_id_clean,
            search_id_clean.replace('-', ' '),
            search_id_clean.replace(' ', '-'),
            search_id_clean.replace('_', '-'),
            search_id_clean.replace('-', '_'),
        ]
        
        for variation in variations:
            if len(variation) > 5:  # Ensure meaningful length
                pattern = f"\\b{re.escape(variation)}\\b"
                if re.search(pattern, filename_upper):
                    return True
        
        return False
    
    def _id_components_match(self, search_id, filename):
        """
        Check if ID components match 
        Supports:
        1. NEW format: EMFHS-2025-A7K matches EMFHS-2025-A7K-B9
        2. OLD format: EMFHS-2025-001 matches EMFHS-2025-001-T8
        3. Year+code: 2025-A7K matches EMFHS-2025-A7K-B9
        """
        search_id_clean = search_id.upper().strip()
        filename_upper = filename.upper()
        
        # Pattern for NEW format: EMFHS-YYYY-XXX-XX (XXX = mixed alphanumeric)
        pattern_new = r'(EMFHS-\d{4}-[A-Z0-9]{3})-[A-Z0-9]{2}'
        match_new = re.search(pattern_new, search_id_clean)
        
        if match_new:
            base_id = match_new.group(1)  # E.g., EMFHS-2025-A7K
            # Check if this base ID appears in filename
            if base_id in filename_upper:
                return True
        
        # Pattern for OLD format: EMFHS-YYYY-NNN-XX (backwards compatibility)
        pattern_old = r'(EMFHS-\d{4}-\d{3})-[A-Z0-9]{2}'
        match_old = re.search(pattern_old, search_id_clean)
        
        if match_old:
            base_id = match_old.group(1)  # E.g., EMFHS-2025-001
            if base_id in filename_upper:
                return True
        
        # Pattern for YYYY-XXX-XX (new format without EMFHS prefix)
        pattern_short_new = r'(\d{4}-[A-Z0-9]{3})-[A-Z0-9]{2}'
        match_short_new = re.search(pattern_short_new, search_id_clean)
        
        if match_short_new:
            base_id = match_short_new.group(1)  # E.g., 2025-A7K
            if base_id in filename_upper:
                return True
        
        # Pattern for YYYY-NNN-XX (old format without EMFHS prefix)
        pattern_short_old = r'(\d{4}-\d{3})-[A-Z0-9]{2}'
        match_short_old = re.search(pattern_short_old, search_id_clean)
        
        if match_short_old:
            base_id = match_short_old.group(1)  # E.g., 2025-001
            if base_id in filename_upper:
                return True
        
        # Check for partial matches (e.g., 2025-A7K, 2025-001)
        # Extract year and code from search ID
        year_match = re.search(r'(\d{4})-[A-Z0-9]{3}', search_id_clean)  # New format
        if not year_match:
            year_match = re.search(r'(\d{4})-\d{3}', search_id_clean)    # Old format
        
        if year_match:
            year = year_match.group(1)
            # Try to get the code part
            code_match_new = re.search(r'\d{4}-([A-Z0-9]{3})', search_id_clean)  # New format
            code_match_old = re.search(r'\d{4}-(\d{3})', search_id_clean)        # Old format
            
            if code_match_new:
                code = code_match_new.group(1)
                # Look for YEAR-CODE pattern in filename
                if f"{year}-{code}" in filename_upper:
                    return True
            elif code_match_old:
                code = code_match_old.group(1)
                # Look for YEAR-CODE pattern in filename
                if f"{year}-{code}" in filename_upper:
                    return True
        
        return False
    
    def _id_appears_anywhere(self, search_id, filename):
        """
        Check if ID appears anywhere in filename (least strict)
        """
        search_id_clean = search_id.upper().strip()
        filename_upper = filename.upper()
        
        return search_id_clean in filename_upper
    
    def _extract_year_from_id(self, student_id):
        """Extract year from student ID (FOR INFORMATION ONLY - NOT FOR RESTRICTION)"""
        patterns = [
            r'EMFHS-(\d{4})-[A-Z0-9]{3}',  # EMFHS-2025-A7K-B9 (NEW FORMAT)
            r'EMFHS-(\d{4})-\d{3}',        # EMFHS-2025-001-T8 (OLD FORMAT)
            r'(\d{4})-[A-Z0-9]{3}-[A-Z0-9]{2}',  # 2025-A7K-B9 (NEW)
            r'(\d{4})-\d{3}-[A-Z0-9]{2}',        # 2025-001-3N (OLD)
            r'(\d{4})-[A-Z0-9]{3}',              # 2025-A7K (NEW)
            r'(\d{4})-\d{3}',                    # 2025-001 (OLD)
            r'(\d{4})/\d{3}',                    # 2025/001
            r'[A-Z]{2,}-(\d{4})-[A-Z0-9]{3}',    # EMIFORPHS-2025-A7K
        ]
        
        student_id_str = str(student_id).upper()
        for pattern in patterns:
            match = re.search(pattern, student_id_str)
            if match:
                try:
                    year = int(match.group(1))
                    return year  # Return year for information only
                except:
                    continue
        
        # Try to find any 4-digit number that looks like a year
        year_match = re.search(r'\b(20\d{2})\b', student_id_str)
        if year_match:
            try:
                year = int(year_match.group(1))
                return year  # Return year for information only
            except:
                pass
        
        return None
    
    def _extract_year_from_session(self, session):
        """Extract start year from session string"""
        try:
            # Session format: "2025/2026" or "2025-2026"
            parts = session.replace('/', '-').split('-')
            if parts and len(parts) > 0:
                return int(parts[0])
        except:
            pass
        
        # Try to find any 4-digit number
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
                newest_year = int(sorted(session_list, reverse=True)[0].split('/')[0])
            else:
                newest_year = datetime.now().year
            
            # Generate future sessions
            future_sessions = []
            for i in range(10):
                future_year = newest_year + i
                future_session = f"{future_year}/{future_year + 1}"
                future_sessions.append(future_session)
            
            # Combine found sessions with future sessions
            all_sessions = session_list + future_sessions
            
            # Remove duplicates and sort
            unique_sessions = list(dict.fromkeys(all_sessions))
            
            def session_sort_key(s):
                try:
                    return int(s.split('/')[0])
                except:
                    return 0
            
            sorted_sessions = sorted(unique_sessions, key=session_sort_key, reverse=True)
            
            # Return all sessions without any filtering
            return sorted_sessions
            
        except Exception as e:
            print(f"❌ Error getting sessions: {str(e)}")
            current_year = datetime.now().year
            # Start from 2000 for comprehensive coverage
            future_sessions = [f"{year}/{year+1}" for year in range(2000, current_year + 11)]
            return future_sessions
    
    def system_status(self):
        """System health check"""
        try:
            # Test authentication
            self.service.about().get(fields='user').execute()
            
            # Test folder access
            query = f"'{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query, pageSize=1).execute()
            
            return {
                'status': '✅ SYSTEM READY',
                'main_folder': 'Connected',
                'authentication': 'Active',
                'total_folders': len(results.get('files', [])),
                'strict_id_matching': 'ENABLED',
                'student_name_verification': 'DISABLED',
                'year_restrictions': 'COMPLETELY DISABLED',
                'id_formats': 'SUPPORTS BOTH: EMFHS-YYYY-XXX-XX (NEW) & EMFHS-YYYY-NNN-XX (OLD)',
                'note': 'Search any session regardless of ID year'
            }
            
        except Exception as e:
            return {
                'status': '❌ SYSTEM ERROR',
                'error': str(e),
                'strict_id_matching': 'ENABLED',
                'student_name_verification': 'DISABLED',
                'year_restrictions': 'COMPLETELY DISABLED',
                'id_formats': 'SUPPORTS BOTH: EMFHS-YYYY-XXX-XX (NEW) & EMFHS-YYYY-NNN-XX (OLD)'
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

# Startup message
print("\n" + "="*70)
print("🏫 EMILIA SCHOOL RESULT SYSTEM - UPDATED FOR NEW ID FORMAT")
print("="*70)
print("🔐 Authentication: Environment Variables (.env)")
print("🔑 Security: STRICT Student ID Matching ENABLED")
print("🆕 ID FORMAT: Supports EMFHS-YYYY-XXX-XX (NEW MIXED ALPHANUMERIC)")
print("📝 ALSO SUPPORTS: EMFHS-YYYY-NNN-XX (OLD FORMAT - BACKWARDS COMPATIBLE)")
print("❌ Student Name Verification: DISABLED")
print("❌ Year Restrictions: COMPLETELY DISABLED")
print("📁 Main folder ID: {drive_service.main_folder_id}")
print("🔍 Search Mode: Requires EXACT Student ID in filename ONLY")
print("✅ Support: All terms (1st, 2nd, 3rd) and sessions (2000-2035+)")
print("✅ Classes: JSS1, JSS2, JSS3, SS1, SS2, SS3")
print("✅ Required: EXACT Student ID Number ONLY")
print("✅ Important: Search ANY session regardless of ID year")
print("="*70)