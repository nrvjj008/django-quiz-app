from django.contrib.auth.models import User

# Create your models here.
from django.db import models


class QuizCategory(models.Model):
    category_name = models.CharField(max_length=50)
    category_id = models.IntegerField()

    def __str__(self):
        return self.category_name


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    quiz_category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=200)

    def __str__(self):
        return self.question_text


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz_category.category_name}"