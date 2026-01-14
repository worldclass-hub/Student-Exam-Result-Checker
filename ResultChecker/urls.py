from django.urls import path
from django.conf.urls.i18n import set_language
from django.views.generic import RedirectView

from . import views  # Make sure to import views here

urlpatterns = [
  
    # Redirect default Django login URL to your custom login page
    path('accounts/login/', RedirectView.as_view(pattern_name='login_page', permanent=False)),
    
    # Authentication
    path('login/', views.login_view, name='login_page'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main page (protected with login_required)
    path('', views.general_exam_page, name="general_exam_page"),

    # Core functions
    path('search/', views.search_result, name='search'),
    path('download/', views.download_pdf, name='download'),
    path('preview/', views.preview_pdf, name='preview'),
    
    # Session management
    path('get_sessions/', views.get_sessions, name='get_sessions'),
    path('generate_sessions/', views.generate_sessions, name='generate_sessions'),
    
    # Testing and debugging
    path('test/', views.test_folder_structure, name='test_folder_structure'),
    path('status/', views.system_status, name='status'),
    path('debug/', views.debug_search, name='debug'),
    path('batch_test/', views.batch_test, name='batch_test'),
    
    # API documentation/health check
    path('api/health/', views.system_status, name='api_health'),
]



