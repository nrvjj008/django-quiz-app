from django.urls import path
from .views import home, start_quiz, quiz_results, quiz_result

app_name = 'quiz'

urlpatterns = [
    path('', home, name='home'),
    path('<int:category_id>/', start_quiz, name='start_quiz'),
    path('quiz-result/<int:quiz_result_id>/', quiz_result, name='quiz_result'),
    path('quiz/results/', quiz_results, name='quiz_results'),
    # ... other URL patterns ...
]
