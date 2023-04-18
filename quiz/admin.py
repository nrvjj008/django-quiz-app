from django.contrib import admin

from .models import QuizCategory, Question

@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'category_id']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz_category', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
