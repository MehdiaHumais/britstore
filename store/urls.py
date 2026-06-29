from django.urls import path

from store import views, views_api

webauthn_patterns = [
    path('webauthn/register/begin/', views.webauthn_register_begin, name='webauthn_register_begin'),
    path('webauthn/register/complete/', views.webauthn_register_complete, name='webauthn_register_complete'),
    path('webauthn/login/begin/', views.webauthn_login_begin, name='webauthn_login_begin'),
    path('webauthn/login/complete/', views.webauthn_login_complete, name='webauthn_login_complete'),
    path('webauthn/status/', views.fingerprint_status, name='fingerprint_status'),
    path('profile/attach-email/', views.attach_email_password, name='attach_email_password'),
]

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('app/<slug:slug>/', views.app_detail, name='app_detail'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('search/', views.search_view, name='search'),
    path('downloads/', views.downloads_view, name='downloads'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),

    # Downloads (login required)
    path('download/<slug:slug>/', views.download_app, name='download_app'),
    path('download/<slug:slug>/v/<str:version>/', views.download_version, name='download_version'),

    # Dashboard
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/apps/', views.dashboard_apps, name='dashboard_apps'),
    path('dashboard/upload/', views.upload_app, name='dashboard_upload'),
    path('dashboard/apps/<slug:slug>/edit/', views.edit_app, name='dashboard_edit_app'),
    path('dashboard/apps/<slug:slug>/delete/', views.delete_app, name='dashboard_delete_app'),
    path('dashboard/apps/<slug:slug>/publish/', views.toggle_publish, name='dashboard_toggle_publish'),
    path('dashboard/apps/<slug:slug>/screenshots/add/', views.add_screenshot, name='dashboard_add_screenshot'),
    path('dashboard/apps/<slug:slug>/screenshots/<int:pk>/delete/', views.delete_screenshot, name='dashboard_delete_screenshot'),
    path('dashboard/apps/<slug:slug>/versions/add/', views.add_version, name='dashboard_add_version'),
    path('dashboard/apps/<slug:slug>/versions/<int:pk>/delete/', views.delete_version, name='dashboard_delete_version'),
    path('dashboard/analytics/', views.analytics_view, name='dashboard_analytics'),
    path('dashboard/categories/', views.manage_categories, name='dashboard_categories'),
    path('dashboard/categories/add/', views.category_create, name='dashboard_category_create'),
    path('dashboard/categories/<int:pk>/edit/', views.category_edit, name='dashboard_category_edit'),
    path('dashboard/categories/<int:pk>/delete/', views.category_delete, name='dashboard_category_delete'),
    path('dashboard/users/', views.manage_users, name='dashboard_users'),
    path('dashboard/users/add/', views.user_create, name='dashboard_user_create'),
    path('dashboard/users/<int:pk>/edit/', views.user_edit, name='dashboard_user_edit'),
    path('dashboard/users/<int:pk>/delete/', views.user_delete, name='dashboard_user_delete'),
    path('dashboard/settings/', views.website_settings, name='dashboard_settings'),
    path('dashboard/api-tokens/', views.manage_api_tokens, name='dashboard_api_tokens'),
    path('dashboard/api-tokens/create/', views.create_api_token, name='dashboard_api_token_create'),
    path('dashboard/api-tokens/<int:pk>/revoke/', views.revoke_api_token, name='dashboard_api_token_revoke'),
    path('dashboard/api-tokens/<int:pk>/regenerate/', views.regenerate_api_token, name='dashboard_api_token_regenerate'),
    path('dashboard/messages/', views.contact_messages, name='dashboard_messages'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('rate/', views.rate_app, name='rate_app'),
    path('search_ajax/', views.search_ajax, name='search_ajax'),

    # ── Update API ──
    path('api/apps/<str:package_name>/check-update/', views_api.check_update, name='api_check_update'),
    path('api/apps/<str:package_name>/download-latest/', views_api.download_latest, name='api_download_latest'),
    path('api/apps/<str:package_name>/release-notes/', views_api.release_notes, name='api_release_notes'),
    path('api/upload-release/', views_api.upload_release, name='api_upload_release'),
]

android_fingerprint_patterns = [
    path('api/fingerprint/android/signup/', views.android_fingerprint_signup, name='android_fp_signup'),
    path('api/fingerprint/android/login/', views.android_fingerprint_login, name='android_fp_login'),
    path('api/fingerprint/android/register/', views.android_fingerprint_register, name='android_fp_register'),
    path('api/fingerprint/android/status/', views.android_fingerprint_status, name='android_fp_status'),
]

urlpatterns += webauthn_patterns
urlpatterns += android_fingerprint_patterns
