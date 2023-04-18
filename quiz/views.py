import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import QuizCategory, Question, QuizResult
from django.db.models import Avg, Max, Min

from django.shortcuts import render
from .models import QuizCategory


@login_required
def home(request):
    quiz_categories = QuizCategory.objects.all()
    return render(request, 'quiz/home.html', {'quiz_categories': quiz_categories})


@login_required
def start_quiz(request, category_id):
    selected_questions = Question.objects.filter(quiz_category__category_id=category_id)
    quiz_topic = QuizCategory.objects.filter(id=category_id).values_list('category_name', flat=True).first()
    if len(selected_questions) > 5:
        selected_questions = random.sample(list(selected_questions), 5)

    # Shuffle the options for each question
    for question in selected_questions:
        options = [question.option1, question.option2, question.option3, question.option4]
        random.shuffle(options)
        question.option1, question.option2, question.option3, question.option4 = options

    if request.method == 'POST':
        # Retrieve the quiz questions based on the category ID
        score = 0
        total_questions = 0

        # Loop through the questions and calculate the score
        for question in selected_questions:
            selected_option = request.POST.get(str(question.id))
            if selected_option == question.correct_answer:
                score += 1
            total_questions += 1

        # Calculate the percentage score
        percentage_score = (score / total_questions) * 100

        # Create a new QuizResult object and save it to the database
        quiz_result = QuizResult.objects.create(
            user=request.user,
            quiz_category_id=category_id,
            score=percentage_score
        )
        quiz_result.save()

        # Render the results template
        context = {
            'quiz_result': quiz_result,
            'category_id':category_id
        }
        return render(request, 'quiz/result.html', context)

    else:
        context = {
            'questions': selected_questions,
            'category_id': category_id,
            'quiz_topic':quiz_topic
        }
        return render(request, 'quiz/question.html', context)


@login_required
def quiz_result(request):
    # Retrieve the latest QuizResult object for the logged in user
    quiz_result = QuizResult.objects.filter(user=request.user).latest('date_taken')
    context = {
        'quiz_result': quiz_result,
    }
    return render(request, 'quiz/result.html', context)

@login_required
def quiz_results(request):
    results = QuizResult.objects.filter(user=request.user)
    context = {'results': results}

    # Calculate average score
    average_score = "{:.2f}".format(results.aggregate(Avg('score'))['score__avg'])
    context['average_score'] = average_score

    # Calculate highest score
    highest_score = "{:.2f}".format(results.aggregate(Max('score'))['score__max'])
    context['highest_score'] = highest_score

    # Calculate lowest score
    lowest_score = "{:.2f}".format(results.aggregate(Min('score'))['score__min'])
    context['lowest_score'] = lowest_score

    return render(request, 'quiz/results.html', context)
