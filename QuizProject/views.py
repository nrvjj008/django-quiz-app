from django.shortcuts import render, redirect

def handler404(request):
    return redirect('quiz:home')