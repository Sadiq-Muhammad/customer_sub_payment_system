from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import datetime, timedelta
import json

@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'subscriptions/user_list.html', {'users': users})

@login_required
def add_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        phone_number = request.POST['phone_number']
        duration = int(request.POST.get('duration', 0))  # Get the duration from the button clicked

        # Calculate the subscription expiry date
        subscription_expiry = datetime.now().date() + timedelta(days=duration * 30)

        # Save the user
        User.objects.create(
            username=username,
            password=password,
            phone_number=phone_number,
            subscription_expiry=subscription_expiry,
        )
        return redirect('user_list')  # Redirect to user list
    return render(request, 'subscriptions/add_user.html')

@login_required
def edit_user(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        duration = int(request.POST.get('duration', 0))  # Get the duration from the button clicked
        user.subscription_expiry = datetime.now().date() + timedelta(days=duration * 30)
        user.save()
        return redirect('user_list')
    return render(request, 'subscriptions/edit_user.html', {'user': user})

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('user_list')

SESSION_TIMEOUT = timedelta(minutes=30)  # Timeout duration

@csrf_exempt
def api_authenticate_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        try:
            user = User.objects.get(username=username, password=password)
            
            # Check subscription expiry
            if user.subscription_expiry < now().date():
                return JsonResponse({'status': 'expired', 'expiry_date': user.subscription_expiry})

            # Handle session timeout
            if user.is_logged_in:
                if user.last_activity and now() - user.last_activity > SESSION_TIMEOUT:
                    # Reset login status if timed out
                    user.is_logged_in = False
                    user.save()
                else:
                    return JsonResponse({'status': 'already_logged_in'})

            # Log the user in
            user.is_logged_in = True
            user.last_activity = now()
            user.save()
            return JsonResponse({'status': 'success', 'expiry_date': user.subscription_expiry})
        except User.DoesNotExist:
            return JsonResponse({'status': 'invalid_credentials'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@csrf_exempt
def api_logout_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        try:
            user = User.objects.get(username=username)
            user.is_logged_in = False
            user.last_activity = None
            user.save()
            return JsonResponse({'status': 'logged_out'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'invalid_user'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user_list')  # Redirect to user list after login
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'subscriptions/login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout
