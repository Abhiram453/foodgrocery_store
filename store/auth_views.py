from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django import forms
from django.utils.http import url_has_allowed_host_and_scheme


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'GET' and next_url:
        storage = messages.get_messages(request)
        has_warning = any(m.level == messages.WARNING for m in storage)
        storage.used = False
        if not has_warning:
            if '/cart' in next_url:
                messages.warning(request, 'Please log in to access your cart.')
            elif '/checkout' in next_url:
                messages.warning(request, 'Please log in to proceed to checkout.')
            elif '/account' in next_url or '/orders' in next_url:
                messages.warning(request, 'Please log in to access your account.')
            else:
                messages.warning(request, 'Please log in to access this page.')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}! 👋')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to FoodBasket, {user.username}! 🎉')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
