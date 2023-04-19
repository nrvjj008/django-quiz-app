from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import  SignUpForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('quiz:home')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        return redirect('quiz:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('quiz:home')
    else:
        form = SignUpForm()
    return render(request, 'authentication/signup.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('login')
