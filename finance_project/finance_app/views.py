from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .models import Transaction
from .forms import TransactionForm
import json
from django.contrib.auth import logout

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'finance_app/dashboard.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'finance_app/add_transaction.html', {'form': form})

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'finance_app/edit_transaction.html', {'form': form})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'finance_app/delete_transaction.html', {'transaction': transaction})

@login_required
def analytics(request):
    # Monthly totals
    monthly_data = Transaction.objects.filter(user=request.user)\
        .annotate(month=TruncMonth('date'))\
        .values('month', 'transaction_type')\
        .annotate(total=Sum('amount'))\
        .order_by('month')

    # Prepare data for charts
    months = []
    income_data = []
    expense_data = []
    
    for entry in monthly_data:
        month_str = entry['month'].strftime('%B %Y')
        if month_str not in months:
            months.append(month_str)
        
        if entry['transaction_type'] == 'income':
            income_data.append(float(entry['total']))
        else:
            expense_data.append(float(entry['total']))

    # Calculate totals
    total_income = Transaction.objects.filter(
        user=request.user, 
        transaction_type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_expenses = Transaction.objects.filter(
        user=request.user, 
        transaction_type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'months': json.dumps(months),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses
    }
    
    return render(request, 'finance_app/analytics.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# Create your views here.
