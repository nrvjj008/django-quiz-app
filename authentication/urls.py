from django.urls import path

from . import views
from .views import login_view, logout_view

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout')
]