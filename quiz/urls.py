from django.urls import path
from .views import home, start_quiz, quiz_results

app_name = 'quiz'

urlpatterns = [
    path('', home, name='home'),
    path('<int:category_id>/', start_quiz, name='start_quiz'),
    path('quiz/results/', quiz_results, name='quiz_results')
]
