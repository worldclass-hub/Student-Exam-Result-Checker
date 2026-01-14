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


@login_required
def general_exam_page(request):
    """Main page for parents to search results"""
    return render(request, "drive_search/general_page.html")

# views.py - COMPLETE FINAL VERSION
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
    # Get available sessions from Drive
    try:
        available_sessions = drive_service.get_available_sessions()
    except Exception as e:
        print(f"⚠️ Error getting sessions: {e}")
        # Generate sessions locally
        current_year = datetime.now().year
        available_sessions = [f"{year}/{year+1}" for year in range(2025, current_year + 11)]
    
    # Get system status
    status = drive_service.system_status()
    
    return render(request, "home.html", {
        'available_sessions': available_sessions,
        'system_status': status
    })

# ============ SEARCH FUNCTION ============
@csrf_exempt
def search_result(request):
    """Handle search with term and session"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_name = data.get('student_name', '').strip()
        student_class = data.get('student_class', '').strip()
        term = data.get('term', '1').strip()
        session = data.get('session', '2025/2026').strip()
        
        print(f"\n🔍 SEARCH REQUEST: {student_name} | {student_class} | Term {term} | {session}")
        
        # Validate
        if not student_name:
            return JsonResponse({
                'success': False,
                'message': 'Please enter student name'
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
        
        # Search Drive
        pdf_files = drive_service.search_student_pdf(term, session, student_class, student_name)
        
        if pdf_files:
            return JsonResponse({
                'success': True,
                'files': pdf_files,
                'count': len(pdf_files),
                'message': f'Found {len(pdf_files)} result(s) for {student_name} in {student_class}'
            })
        else:
            return JsonResponse({
                'success': False,
                'files': [],
                'count': 0,
                'message': f'No results found for "{student_name}" in {student_class}. '
                          f'Please check: 1) Student name spelling 2) Correct class 3) Correct term/session'
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
                'is_past': session_year < current_academic_start
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_with_labels,
            'current_session': current_academic_session,
            'total': len(sessions)
        })
    except Exception as e:
        print(f"❌ Error getting sessions: {e}")
        # Generate sessions locally
        current_year = datetime.now().year
        sessions = [f"{year}/{year+1}" for year in range(2025, current_year + 11)]
        
        sessions_with_labels = [{'value': s, 'label': s} for s in sessions]
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_with_labels,
            'current_session': f"{current_year}/{current_year+1}",
            'total': len(sessions),
            'note': 'Generated locally due to error'
        })

@csrf_exempt
def generate_sessions(request):
    """Generate future academic sessions"""
    current_year = datetime.now().year
    
    # Generate sessions from 2025 to 20 years in the future
    sessions = []
    for year in range(2025, current_year + 21):
        sessions.append(f"{year}/{year + 1}")
    
    # Add labels
    sessions_with_labels = []
    for session in sessions:
        sessions_with_labels.append({
            'value': session,
            'label': session
        })
    
    return JsonResponse({
        'success': True,
        'sessions': sessions_with_labels,
        'generated': len(sessions),
        'note': 'Generated future sessions locally'
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
            'sample_pdfs': [pdf['name'] for pdf in pdfs[:3]]
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
            }
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
    """Test multiple search scenarios"""
    test_cases = [
        {'term': '1', 'session': '2025/2026', 'class': 'JSS1', 'student': 'Sample'},
        {'term': '2', 'session': '2025/2026', 'class': 'JSS2', 'student': 'Sample'},
        {'term': '3', 'session': '2025/2026', 'class': 'SS1', 'student': 'Sample'},
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
        'failed': sum(1 for r in results if r['status'] == '❌ Failed')
    })










from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json

def login_view(request):
    """
    Handle login requests from the portal
    """
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('/')  # Redirect to home page if already logged in
    
    if request.method == 'POST':
        # Check if it's an AJAX request (from mobile)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful! Welcome to Emilia Foremost High School Portal.',
                        'redirect_url': '/'  # Redirect to home page
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid username or password. Please try again.'
                    })
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid request format.'
                })
        
        # Regular form submission (desktop)
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful! Welcome to Emilia Foremost High School Portal.')
            return redirect('/')  # Redirect to home page
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('login_page')
    
    # GET request - show login page
    return render(request, 'drive_search/student_portal.html')

def logout_view(request):
    """
    Handle logout requests
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login_page')
