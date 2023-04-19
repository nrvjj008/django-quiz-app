from django.urls import path

from authentication import views
from authentication.views import logout_view

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.login_view, name='login'),
    path('logout/', logout_view, name='logout')
]