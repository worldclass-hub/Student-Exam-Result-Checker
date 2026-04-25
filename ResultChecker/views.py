# ResultChecker/views.py - COMPLETE VERSION
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
import json
from .drive_service import drive_service
from googleapiclient.http import MediaIoBaseDownload
import io
import traceback
from django.conf import settings
from django.contrib.auth.decorators import login_required  # ADD THIS IMPORT















# views.py - UPDATED FOR NEW ID FORMAT: EMFHS-YYYY-XXX-XX
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from googleapiclient.http import MediaIoBaseDownload
import io
from .drive_service import drive_service

# ============ MAIN PAGE ============
def home_page(request):
    """Main page for parents"""
    try:
        available_sessions = drive_service.get_available_sessions()
    except Exception as e:
        print(f"⚠️ Error getting sessions: {e}")
        current_year = datetime.now().year
        available_sessions = [f"{year}/{year+1}" for year in range(2000, current_year + 11)]
    
    status = drive_service.system_status()
    
    return render(request, "home.html", {
        'available_sessions': available_sessions,
        'system_status': status
    })

# ============ SEARCH FUNCTION - SUPPORTS NEW ID FORMAT ============
@csrf_exempt
def search_result(request):
    """Handle search with NO YEAR RESTRICTIONS - SUPPORTS NEW ID FORMAT"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_name = data.get('student_name', '').strip()
        student_id = data.get('student_id', '').strip()
        student_class = data.get('student_class', '').strip()
        term = data.get('term', '1').strip()
        session = data.get('session', '2025/2026').strip()
        
        print(f"\n🔍 SEARCH (NEW ID FORMAT SUPPORTED):")
        print(f"   🔑 ID: {student_id}")
        print(f"   🆕 Format: EMFHS-YYYY-XXX-XX (mixed alphanumeric)")
        print(f"   🏫 Class: {student_class}")
        print(f"   📅 Term: {term} | Session: {session}")
        print(f"   ⚠️  Note: Year matching is DISABLED")
        
        # Validate
        if not student_id:
            return JsonResponse({
                'success': False,
                'message': 'Student ID is required'
            })
        
        if not student_class:
            return JsonResponse({
                'success': False,
                'message': 'Please select class'
            })
        
        # Validate session format
        if '/' not in session:
            return JsonResponse({
                'success': False,
                'message': 'Invalid session format. Use format: YYYY/YYYY'
            })
        
        # Extract year from ID for information only (NO RESTRICTION)
        student_id_year = drive_service._extract_year_from_id(student_id)
        session_start_year = drive_service._extract_year_from_session(session)
        
        # Search Drive with NEW ID FORMAT SUPPORT
        pdf_files = drive_service.search_student_pdf(
            term, 
            session, 
            student_class, 
            student_name,  # Name is passed but NOT USED for verification
            student_id
        )
        
        if pdf_files:
            return JsonResponse({
                'success': True,
                'files': pdf_files,
                'count': len(pdf_files),
                'student_id': student_id,
                'student_id_year': student_id_year,
                'session_year': session_start_year,
                'strict_id_matching': True,
                'student_name_verification': False,
                'year_restrictions': False,
                'id_format': 'NEW: EMFHS-YYYY-XXX-XX (mixed alphanumeric)',
                'message': f'Found {len(pdf_files)} result(s) with ID: {student_id}'
            })
        else:
            # Helpful error message with new ID format examples
            error_msg = f'No results found with Student ID: {student_id} in {student_class}. '
            
            error_msg += 'Please check: '
            error_msg += '1) Exact Student ID spelling '
            error_msg += '2) Correct class selection '
            error_msg += '3) Correct term/session '
            error_msg += '4) Try both old and new ID formats if needed '
            
            # Add format guidance
            format_note = ''
            if student_id_year:
                format_note = f'Your ID ({student_id}) appears to be from year {student_id_year}. '
                format_note += 'New ID format: EMFHS-YYYY-XXX-XX (e.g., EMFHS-2025-A7K-B9) '
                format_note += 'Old ID format: EMFHS-YYYY-NNN-XX (e.g., EMFHS-2025-001-A4)'
            
            return JsonResponse({
                'success': False,
                'files': [],
                'count': 0,
                'message': error_msg,
                'format_note': format_note,
                'student_id_year': student_id_year,
                'session_year': session_start_year,
                'strict_id_matching': True,
                'student_name_verification': False,
                'year_restrictions': False,
                'id_format': 'Supports both old and new formats'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data'
        }, status=400)
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Search failed. Please try again.'
        }, status=500)

# ============ DOWNLOAD FUNCTION ============
@csrf_exempt
def download_pdf(request):
    """Download PDF file"""
    file_id = request.GET.get('file_id')
    
    if not file_id:
        return JsonResponse({'error': 'No file selected'}, status=400)
    
    try:
        file_info = drive_service.get_file_info(file_id)
        filename = file_info.get('name', 'result.pdf')
        
        # Download from Drive
        request_drive = drive_service.service.files().get_media(fileId=file_id)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        downloader = MediaIoBaseDownload(response, request_drive)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        return response
        
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ============ UTILITY FUNCTIONS ============
@csrf_exempt
def get_sessions(request):
    """Get available sessions"""
    try:
        sessions = drive_service.get_available_sessions()
        
        # Add labels for frontend
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Determine current academic year
        if current_month >= 8:  # September or later
            current_academic_start = current_year
        else:
            current_academic_start = current_year - 1
        
        current_academic_session = f"{current_academic_start}/{current_academic_start + 1}"
        
        sessions_with_labels = []
        for session in sessions:
            label = session
            session_year = int(session.split('/')[0])
            
            if session == current_academic_session:
                label += " (Current)"
            elif session_year > current_academic_start:
                label += " (Upcoming)"
            elif session_year < current_academic_start:
                label += " (Past)"
            
            sessions_with_labels.append({
                'value': session,
                'label': label,
                'is_current': session == current_academic_session,
                'is_future': session_year > current_academic_start,
                'is_past': session_year < current_academic_start,
                'start_year': session_year
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_with_labels,
            'current_session': current_academic_session,
            'total': len(sessions),
            'year_restriction': 'DISABLED',
            'min_year': 2000,
            'id_format': 'SUPPORTS: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)',
            'note': 'Search any session regardless of ID year'
        })
    except Exception as e:
        print(f"❌ Error getting sessions: {e}")
        # Generate sessions locally
        current_year = datetime.now().year
        sessions = [f"{year}/{year+1}" for year in range(2000, current_year + 11)]
        
        sessions_with_labels = [{'value': s, 'label': s} for s in sessions]
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_with_labels,
            'current_session': f"{current_year}/{current_year+1}",
            'total': len(sessions),
            'note': 'Generated locally due to error',
            'id_format': 'SUPPORTS: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)',
            'year_restriction': 'DISABLED'
        })

@csrf_exempt
def generate_sessions(request):
    """Generate future academic sessions"""
    current_year = datetime.now().year
    
    sessions = []
    for year in range(2000, current_year + 21):
        sessions.append(f"{year}/{year + 1}")
    
    sessions_with_labels = []
    for session in sessions:
        sessions_with_labels.append({
            'value': session,
            'label': session,
            'start_year': int(session.split('/')[0])
        })
    
    return JsonResponse({
        'success': True,
        'sessions': sessions_with_labels,
        'generated': len(sessions),
        'note': 'Generated future sessions locally',
        'min_year': 2000,
        'id_format': 'SUPPORTS: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)',
        'year_restriction': 'DISABLED'
    })

@csrf_exempt
def test_folder_structure(request):
    """Test if folder structure is accessible"""
    term = request.GET.get('term', '1')
    session = request.GET.get('session', '2025/2026')
    class_name = request.GET.get('class', 'JSS2')
    
    try:
        class_folder_id = drive_service.find_class_folder(term, session, class_name)
        
        # Count PDFs
        query = f"'{class_folder_id}' in parents and mimeType='application/pdf'"
        results = drive_service.service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=5
        ).execute()
        
        pdfs = results.get('files', [])
        
        # Get term folder ID for reference
        term_folder_id = drive_service.find_term_folder(term, session)
        
        return JsonResponse({
            'success': True,
            'term': term,
            'session': session,
            'class': class_name,
            'accessible': True,
            'term_folder_id': term_folder_id,
            'class_folder_id': class_folder_id,
            'pdf_count': len(pdfs),
            'sample_pdfs': [pdf['name'] for pdf in pdfs[:3]],
            'strict_id_matching': True,
            'student_name_verification': False,
            'year_restrictions': False,
            'id_format': 'SUPPORTS: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': f'Failed to access Term {term} {session} {class_name}'
        })

@csrf_exempt
def system_status(request):
    """System health check"""
    try:
        status = drive_service.system_status()
        
        # Get additional info
        sessions = drive_service.get_available_sessions()
        
        return JsonResponse({
            'success': True,
            **status,
            'available_sessions_count': len(sessions),
            'available_sessions_sample': sessions[:10],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'status': '❌ CRITICAL ERROR',
            'error': str(e),
            'message': 'System check failed'
        })

@csrf_exempt
def debug_search(request):
    """Debug endpoint to see folder structure"""
    try:
        # List all folders in main directory
        query = f"'{drive_service.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        results = drive_service.service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=50
        ).execute()
        
        all_folders = results.get('files', [])
        
        # Get system status
        status = drive_service.system_status()
        
        return JsonResponse({
            'success': True,
            'main_folder_id': drive_service.main_folder_id,
            'total_folders': len(all_folders),
            'folders': [{'name': f['name'], 'id': f['id'][:20] + '...'} for f in all_folders],
            'system_status': status,
            'cache_info': {
                'term_folders_cached': len(drive_service.term_folders_cache),
                'class_folders_cached': len(drive_service.class_folders_cache)
            },
            'strict_id_matching': True,
            'student_name_verification': False,
            'year_restrictions': False,
            'id_format': 'SUPPORTS: EMFHS-YYYY-XXX-XX (NEW MIXED FORMAT)'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============ PREVIEW FUNCTION ============
@csrf_exempt
def preview_pdf(request):
    """Generate preview link for PDF"""
    file_id = request.GET.get('file_id')
    
    if not file_id:
        return JsonResponse({'error': 'No file selected'}, status=400)
    
    try:
        # Get file info
        file_info = drive_service.service.files().get(
            fileId=file_id,
            fields="id, name, webViewLink"
        ).execute()
        
        preview_url = file_info.get('webViewLink', f'https://drive.google.com/file/d/{file_id}/view')
        
        return JsonResponse({
            'success': True,
            'preview_url': preview_url,
            'filename': file_info.get('name', 'result.pdf')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ============ BATCH TEST ============
@csrf_exempt
def batch_test(request):
    """Test multiple search scenarios with folder verification"""
    test_cases = [
        {'term': '1', 'session': '2009/2010', 'class': 'JSS1', 'student': 'Sample', 'student_id': 'EMFHS-2009-001'},
        {'term': '2', 'session': '2010/2011', 'class': 'JSS2', 'student': 'Sample', 'student_id': 'EMFHS-2010-002'},
        {'term': '3', 'session': '2025/2026', 'class': 'SS1', 'student': 'Sample', 'student_id': 'EMFHS-2025-A7K-B9'},
        {'term': '1', 'session': '2024/2025', 'class': 'JSS3', 'student': 'Sample', 'student_id': 'EMFHS-2024-C2D-E3'},
    ]
    
    results = []
    
    for test in test_cases:
        try:
            folder_id = drive_service.find_class_folder(
                test['term'], 
                test['session'], 
                test['class']
            )
            results.append({
                **test,
                'status': '✅ Found',
                'folder_id': folder_id[:15] + '...'
            })
        except Exception as e:
            results.append({
                **test,
                'status': '❌ Failed',
                'error': str(e)
            })
    
    return JsonResponse({
        'success': True,
        'tests': results,
        'passed': sum(1 for r in results if r['status'] == '✅ Found'),
        'failed': sum(1 for r in results if r['status'] == '❌ Failed'),
        'strict_id_matching': True,
        'student_name_verification': False,
        'year_restrictions': False,
        'id_format': 'SUPPORTS BOTH OLD AND NEW FORMATS'
    })

# ============ STUDENT RESULT SEARCH PAGE ============
from django.contrib.auth.decorators import login_required

# @login_required
def general_exam_page(request):
    """Render the student result search page"""
    try:
        available_sessions = drive_service.get_available_sessions()
    except Exception as e:
        print(f"⚠️ Error getting sessions: {e}")
        current_year = datetime.now().year
        available_sessions = [f"{year}/{year+1}" for year in range(2000, current_year + 11)]
    
    status = drive_service.system_status()
    
    return render(request, "drive_search/general_page.html", {
        'available_sessions': available_sessions,
        'system_status': status
    })











# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import JsonResponse
# import json

# def login_view(request):
#     """
#     Handle login requests from the portal
#     """
#     # Check if user is already logged in
#     if request.user.is_authenticated:
#         return redirect('/')  # Redirect to home page if already logged in
    
#     if request.method == 'POST':
#         # Check if it's an AJAX request (from mobile)
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             try:
#                 data = json.loads(request.body)
#                 username = data.get('username')
#                 password = data.get('password')
                
#                 user = authenticate(request, username=username, password=password)
                
#                 if user is not None:
#                     login(request, user)
#                     return JsonResponse({
#                         'success': True,
#                         'message': 'Login successful! Welcome to Emilia Foremost High School Portal.',
#                         'redirect_url': '/'  # Redirect to home page
#                     })
#                 else:
#                     return JsonResponse({
#                         'success': False,
#                         'message': 'Invalid username or password. Please try again.'
#                     })
#             except json.JSONDecodeError:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid request format.'
#                 })
        
#         # Regular form submission (desktop)
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         user = authenticate(request, username=username, password=password)
        
#         if user is not None:
#             login(request, user)
#             messages.success(request, 'Login successful! Welcome to Emilia Foremost High School Portal.')
#             return redirect('/')  # Redirect to home page
#         else:
#             messages.error(request, 'Invalid username or password. Please try again.')
#             return redirect('login_page')
    
#     # GET request - show login page
#     return render(request, 'drive_search/student_portal.html')

# def logout_view(request):
#     """
#     Handle logout requests
#     """
#     logout(request)
#     messages.success(request, 'You have been successfully logged out.')
#     return redirect('login_page')




