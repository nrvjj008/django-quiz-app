import random

from django.contrib.auth.decorators import login_required
from .models import Question, QuizResult
from django.db.models import Avg, Max, Min

from django.shortcuts import render
from .models import QuizCategory


@login_required #if not authenitcated then redirect them to login page
def home(request): #home screen that displays all quiz categories
    quiz_categories = QuizCategory.objects.all() #retrive all quiz categories
    return render(request, 'quiz/home.html', {'quiz_categories': quiz_categories}) # pass categories as context


@login_required
def start_quiz(request, category_id):
    selected_questions = Question.objects.filter(quiz_category__category_id=category_id) # get questions of the category_id
    quiz_topic = QuizCategory.objects.filter(id=category_id).values_list('category_name', flat=True).first() # to display quiz topic
    if len(selected_questions) == 0:
        # Display an error message if no questions are found
        error_message = 'No questions found.'
        context = {'error_message': error_message}
        return render(request, 'quiz/no_questions_found.html', context)

    if len(selected_questions) > 5:
        selected_questions = random.sample(list(selected_questions), 5) #randomize question of more than 5

    # Shuffle the options for each question
    for question in selected_questions:
        options = [question.option1, question.option2, question.option3, question.option4]
        random.shuffle(options)
        question.option1, question.option2, question.option3, question.option4 = options #reassign shuffled options back

    #this will be called when a user submits the quiz since that is going to be a post request
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

    # when a user starts a quiz, this will be called because the request will be a get request
    else:
        context = {
            'questions': selected_questions,
            'category_id': category_id,
            'quiz_topic':quiz_topic
        }
        return render(request, 'quiz/question.html', context)


@login_required
def quiz_results(request):
    results = QuizResult.objects.filter(user=request.user)
    context = {'results': results}

    avg_score = results.aggregate(Avg('score'))['score__avg']
    highest_score = results.aggregate(Max('score'))['score__max']
    lowest_score = results.aggregate(Min('score'))['score__min']

    if avg_score is not None:
        context['average_score'] =  "{:.2f}".format(avg_score)
    else:
        context['average_score'] = "N/A"

    if highest_score is not None:
        context['highest_score'] = "{:.2f}".format(highest_score)
    else:
        context['highest_score'] = "N/A"

    if lowest_score is not None:
        context['lowest_score'] = "{:.2f}".format(lowest_score)
    else:
        context['lowest_score'] = "N/A"

    return render(request, 'quiz/results.html', context)
