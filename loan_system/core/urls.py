from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply-loan/', views.apply_loan, name='apply_loan'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/approve/<int:loan_id>/', views.approve_loan, name='approve_loan'),
    path('admin-dashboard/reject/<int:loan_id>/', views.reject_loan, name='reject_loan'),
    path('savings/', views.savings_view, name='savings'),
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='reset_password'),
    path('reset-password-sent/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_sent.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset-password-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    path('set-target/', views.set_target, name='set_target'),
    path('target-history/', views.target_history, name='target_history'),
    path('loans/', views.user_loans, name='user_loans'),
    path('admin-savings/', views.admin_savings_view, name='admin_savings'),
    path('welfare/', views.welfare_contribution_view, name='welfare_contribution'),
    path('admin-welfare/', views.admin_welfare_view, name='admin_welfare'),
    
    
  

]

