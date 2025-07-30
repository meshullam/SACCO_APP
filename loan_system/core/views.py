# core/views.py (CLEANED AND FIXED)

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from decimal import Decimal
from datetime import datetime
import calendar
from datetime import timedelta

from .models import Loan, Savings, SavingsTarget

# ---------------------------
# AUTHENTICATION VIEWS
# ---------------------------
def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            user = User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully")
            return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# ---------------------------
# USER DASHBOARD
# ---------------------------
@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    now = datetime.now()
    month = now.month
    year = now.year

    # Monthly savings
    total_savings = Savings.objects.filter(
        user=request.user,
        date_saved__month=month,
        date_saved__year=year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Monthly target
    target_obj = SavingsTarget.objects.filter(user=request.user, month=month, year=year).first()
    target_savings = target_obj.amount if target_obj else 0
    progress = (total_savings / target_savings) * 100 if target_savings else 0
    remaining = max(target_savings - total_savings, 0)

    # Mid-month warning
    mid_month_warning = False
    if now.day >= 15 and total_savings == 0:
        mid_month_warning = True

    # Chart data
    monthly_data = (
        Savings.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date_saved'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    targets_data = SavingsTarget.objects.filter(user=request.user).order_by('year', 'month')

    labels = []
    savings_values = []
    target_values = []

    for t in targets_data:
        label = f"{calendar.month_abbr[t.month]} {t.year}"
        labels.append(label)

        matching = next(
            (s['total'] for s in monthly_data if s['month'].month == t.month and s['month'].year == t.year),
            0
        )
        savings_values.append(float(matching))
        target_values.append(float(t.amount))

    return render(request, 'core/dashboard.html', {
        'total_savings': total_savings,
        'target_savings': target_savings,
        'progress': round(progress, 1),
        'remaining': remaining,
        'mid_month_warning': mid_month_warning,
        'chart_labels': labels,
        'chart_savings': savings_values,
        'chart_targets': target_values,
    })

# ---------------------------
# SAVINGS VIEWS
# ---------------------------
@login_required
def savings_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        messages.success(request, f"Please complete payment of {amount} KES via M-PESA to Paybill 123456, Account: {request.user.username}")

    total_savings = Savings.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'core/savings.html', {
        'total_savings': total_savings
    })

# ---------------------------
# TARGET MODULE
# ---------------------------
@login_required
def set_target(request):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    target = SavingsTarget.objects.filter(
        user=request.user,
        month=current_month,
        year=current_year
    ).first()

    if not target:
        target = SavingsTarget(user=request.user, month=current_month, year=current_year)

    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        target.amount = amount
        target.save()
        messages.success(request, f"Target set to {amount} KES for {now.strftime('%B %Y')}")
        return redirect('dashboard')

    return render(request, 'core/set_target.html', {'target': target})

@login_required
def target_history(request):
    targets = SavingsTarget.objects.filter(user=request.user).order_by('-year', '-month')
    return render(request, 'core/target_history.html', {'targets': targets})

# ---------------------------
# LOAN VIEWS
# ---------------------------
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from .models import Loan, Savings

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import timedelta

from .models import Loan, Savings

@login_required
def apply_loan(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    # Calculate total user savings
    user_savings = Savings.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    loan_limit = user_savings * 3

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        purpose = request.POST.get('purpose')

        if amount > loan_limit:
            messages.error(request, f"You have exceeded your loan limit of KES {loan_limit:.2f}")
            return redirect('apply_loan')

        Loan.objects.create(
            user=request.user,
            amount=amount,
            purpose=purpose,
            status='PENDING',
            due_date=timezone.now().date() + timedelta(days=30)
        )

        messages.success(request, "Loan application submitted successfully.")
        return redirect('user_loans')

    return render(request, 'core/apply_loan.html', {
        'loan_limit': loan_limit
    })



@staff_member_required
def approve_loan(request, loan_id):
    loan = Loan.objects.get(id=loan_id)
    loan.status = 'APPROVED'
    loan.approved_by = request.user
    loan.approval_date = timezone.now()
    loan.save()
    messages.success(request, "Loan approved.")
    return redirect('admin_dashboard')

@staff_member_required
def reject_loan(request, loan_id):
    loan = Loan.objects.get(id=loan_id)
    loan.status = 'REJECTED'
    loan.approved_by = request.user
    loan.approval_date = timezone.now()
    loan.save()
    messages.info(request, "Loan rejected.")
    return redirect('admin_dashboard')

# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@staff_member_required
def admin_dashboard(request):
    status_filter = request.GET.get('status') or 'PENDING'  # Default to PENDING

    if status_filter in ['PENDING', 'APPROVED', 'REJECTED']:
        all_loans = Loan.objects.filter(status=status_filter).order_by('-date_applied')
    else:
        all_loans = Loan.objects.all().order_by('-date_applied')

    loan_counts = Loan.objects.values('status').annotate(count=Count('id'))
    loan_amounts_by_status = Loan.objects.values('status').annotate(total=Sum('amount'))

    return render(request, 'core/admin_dashboard.html', {
        'all_loans': all_loans,
        'loan_counts': loan_counts,
        'loan_amounts': loan_amounts_by_status,
        'selected_status': status_filter,
    })

from django.shortcuts import render
from .models import Loan

@login_required
def user_loans(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    status_filter = request.GET.get('status', 'PENDING')  # Default is PENDING

    user_loans = Loan.objects.filter(user=request.user).order_by('-date_applied')
    if status_filter in ['PENDING', 'APPROVED', 'REJECTED']:
        user_loans = user_loans.filter(status=status_filter)

    return render(request, 'core/user_loans.html', {
        'user_loans': user_loans,
        'selected_status': status_filter,
    })



from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth.models import User
import calendar

from .models import Savings, SavingsTarget

@staff_member_required
def admin_savings_view(request):
    now = timezone.now()
    month = now.month
    year = now.year

    # Get filters from request
    user_filter = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Base savings queryset
    savings_list = Savings.objects.all().order_by('-date_saved')

    # Apply filters
    if user_filter:
        savings_list = savings_list.filter(user__username__icontains=user_filter)
    if start_date:
        savings_list = savings_list.filter(date_saved__date__gte=start_date)
    if end_date:
        savings_list = savings_list.filter(date_saved__date__lte=end_date)

    # Total savings from filtered list
    total_amount = savings_list.aggregate(Sum('amount'))['amount__sum'] or 0

    # Total savings per user (filtered if user search is applied)
    per_user_qs = Savings.objects.all()
    if user_filter:
        per_user_qs = per_user_qs.filter(user__username__icontains=user_filter)

    per_user = per_user_qs.values('user__username').annotate(total=Sum('amount')).order_by('-total')

    # Chart: Monthly savings data
    monthly_data = (
        Savings.objects
        .annotate(month=TruncMonth('date_saved'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    chart_labels = [entry['month'].strftime('%b %Y') for entry in monthly_data]
    chart_data = [float(entry['total']) for entry in monthly_data]

    # Users and their targets
    users = User.objects.filter(is_staff=False)
    user_data = []

    for user in users:
        user_month_savings = Savings.objects.filter(
            user=user,
            date_saved__month=month,
            date_saved__year=year
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        target = SavingsTarget.objects.filter(user=user, month=month, year=year).first()
        target_amount = target.amount if target else 0
        met_target = user_month_savings >= target_amount and target_amount > 0

        user_data.append({
            'user': user,
            'savings': user_month_savings,
            'target': target_amount,
            'met_target': met_target,
        })

    return render(request, 'core/admin_savings.html', {
        'savings_list': savings_list,
        'total_amount': total_amount,
        'per_user': per_user,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'user_data': user_data,
        'month': now.strftime('%B'),
        'year': year,
    })
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.shortcuts import render
from .models import WelfareContribution

@staff_member_required
def admin_welfare_view(request):
    contributions = WelfareContribution.objects.all().order_by('-date_contributed')

    monthly_summary = (
        WelfareContribution.objects
        .annotate(month=TruncMonth('date_contributed'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    return render(request, 'core/admin_welfare.html', {
        'contributions': contributions,
        'monthly_summary': monthly_summary
    })
@login_required
def welfare_contribution_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        WelfareContribution.objects.create(user=request.user, amount=amount)
        messages.success(request, f"Please complete payment of {amount} KES via M-PESA to Paybill 123456, Account: {request.user.username}")
        return redirect('welfare_contribution')

    user_contributions = WelfareContribution.objects.filter(user=request.user).order_by('-date_contributed')
    total_contributed = user_contributions.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'core/welfare_contribution.html', {
        'user_contributions': user_contributions,
        'total_contributed': total_contributed,
    })

from django.utils import timezone
from .models import WelfareContribution
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from decimal import Decimal

@login_required
def welfare_contribute(request):
    now = timezone.now()
    current_month = now.strftime('%B %Y')

    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        WelfareContribution.objects.create(user=request.user, amount=amount)
        messages.success(request, f"Your contribution of KES {amount} has been recorded. Thank you!")
        return redirect('welfare_contribute')

    return render(request, 'core/welfare_contribute.html', {
        'current_month': current_month
    })
from django.contrib.admin.views.decorators import staff_member_required
from .models import WelfareContribution
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.utils import timezone

@staff_member_required
def admin_welfare_view(request):
    # Filters
    user_filter = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    contributions = WelfareContribution.objects.all().order_by('-date_contributed')

    if user_filter:
        contributions = contributions.filter(user__username__icontains=user_filter)
    if start_date:
        contributions = contributions.filter(date_contributed__date__gte=start_date)
    if end_date:
        contributions = contributions.filter(date_contributed__date__lte=end_date)

    # Monthly summary chart data
    monthly_summary = (
        WelfareContribution.objects
        .annotate(month=TruncMonth('date_contributed'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    chart_labels = [entry['month'].strftime('%b %Y') for entry in monthly_summary]
    chart_data = [float(entry['total']) for entry in monthly_summary]

    total_amount = contributions.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'core/admin_welfare.html', {
        'contributions': contributions,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'total_amount': total_amount,
    })





