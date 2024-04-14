from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Q
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django import forms
from django.http import HttpResponse
from pdf2image import convert_from_path
import io
from .serializers import BookDetailSerializer, SignupSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Book, Category
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.mail import send_mail
import random

from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import os
from django.core.files.storage import default_storage
from .models import Book


def download_all_ebook_pdfs():
    # Get all Book instances
    books = Book.objects.all()

    # Directory to save the PDFs
    save_directory = "downloaded_pdfs"

    # Create the directory if it doesn't exist
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Loop through each book
    for book in books:
        pdf_name = f"{book.title}.pdf"
        pdf_path = os.path.join("ebooks", str(book.id), pdf_name)

        # Check if the file exists in storage
        if default_storage.exists(pdf_path):
            # If it does, open and save the file
            with default_storage.open(pdf_path, 'rb') as pdf_file:
                with open(os.path.join(save_directory, pdf_name), 'wb') as local_file:
                    local_file.write(pdf_file.read())

@api_view(['GET'])
def list_categories(request):
    categories = Category.objects.all().values('id', 'name')
    return JsonResponse(list(categories), safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def book_list(request):
    categories = Category.objects.all()
    data = {}

    for category in categories:
        books_in_category = Book.objects.filter(category=category).order_by('-created_at')[:10]

        if books_in_category.exists():
            book_list = []
            for book in books_in_category:
                # Check if book has a cover_image before accessing its URL
                cover_image_url = request.build_absolute_uri(book.cover_image.url) if book.cover_image else None
                book_list.append({
                    'id': book.id,
                    'title': book.title,
                    'cover_image': cover_image_url
                })

            data[category.name] = book_list

    return JsonResponse(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def book_detail(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Book not found"}, status=404)

    serializer = BookDetailSerializer(book, context={'request': request})

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_newsletter(request):
    user = request.user
    NewsletterSubscription.objects.update_or_create(user=user, defaults={'subscribed': True})
    return JsonResponse({'status': 'subscribed'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsubscribe_newsletter(request):
    user = request.user
    subscription, created = NewsletterSubscription.objects.get_or_create(user=user)
    subscription.subscribed = False
    subscription.save()
    return JsonResponse({'status': 'unsubscribed'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):
    user = request.user
    subscription = NewsletterSubscription.objects.filter(user=user).first()
    is_subscribed = subscription.subscribed if subscription else False
    return JsonResponse({'is_subscribed': is_subscribed})

@api_view(['POST'])
def contact_us(request):


    if request.method == 'POST':
        email = request.data['email']
        name = request.data['name']
        message = request.data['message']

        Contact.objects.create(email=email, name=name, message=message)
        download_all_ebook_pdfs()


        return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'status': 'bad request'}, status=400)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_books(request, category_id):
    # Fetch the category using ID
    category_ = get_object_or_404(Category, id=category_id)

    # Get all books for the fetched category
    books_in_category = Book.objects.filter(category=category_).order_by('-created_at')

    # Create serialized data list
    serialized_data = []
    for book in books_in_category:
        serialized_data.append({
            'id': book.id,
            'title': book.title,
            'cover_image': request.build_absolute_uri(book.cover_image.url) if book.cover_image else None
        })

    return JsonResponse(serialized_data, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_books(request):
    query = request.GET.get('query', '')
    search_type = request.GET.get('type', 'book')

    if search_type == 'book':
        books = Book.objects.filter(title__icontains=query).order_by('-created_at')
    elif search_type == 'author':
        books = Book.objects.filter(author__icontains=query).order_by('-created_at')
    elif search_type == 'publisher':
        books = Book.objects.filter(publisher__icontains=query).order_by('-created_at')
    else:
        return JsonResponse({"error": "Invalid search type"}, status=400)

    # Paginate the results just like the favorites view
    paginator = Paginator(books, 20)  # Here 20 books per page, adjust as needed
    page = request.GET.get('page', 1)
    current_page_books = paginator.get_page(page)

    # Serialize the data
    serialized_data = [{
        'id': book.id,
        'title': book.title,
        'cover_image': request.build_absolute_uri(book.cover_image.url) if book.cover_image else None
    } for book in current_page_books]

    return JsonResponse(serialized_data, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_book_note(request, book_id):
    # Access the authenticated user directly
    user = request.user

    # First, check if the book with the given book_id exists
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

    # Update or create the note
    note, created = Note.objects.update_or_create(user=user, book=book, defaults={'text': request.data.get('text', '')})

    return Response({"success": True, "message": "Note saved successfully!"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_book_review(request, book_id):
    # Retrieve the book object
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

    # If you're sending 'user' from the frontend, retrieve it. Otherwise, use the authenticated user.
    # Note: Allowing frontend to send 'user' can be a security concern as it can be tampered.
    if 'user' in request.data:
        user_id = request.data['user']
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        user = request.user

    # Collect data for the review
    data = {
        'rating': request.data.get('rating', None),  # Assuming rating is being sent in the request
        'comment': request.data.get('comment', '')   # Assuming comment is being sent in the request
    }

    # Update or create the review
    review, created = Review.objects.update_or_create(user=user, book=book, defaults=data)

    return Response({"success": True, "message": "Review saved successfully!"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, book_id):
    user = request.user
    book = Book.objects.get(pk=book_id)

    if user in book.favorited_by.all():
        # If book is already favorited, remove it
        book.favorited_by.remove(user)
        return Response({"status": "Book removed from favorites"})
    else:
        # If book is not favorited, add it
        book.favorited_by.add(user)
        return Response({"status": "Book added to favorites"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorite_books(request):
    user = request.user
    books = user.favorite_books.all().order_by('-created_at')

    # Paginate the results
    paginator = Paginator(books, 20)  # Here 20 books per page, you can adjust this number
    page = request.GET.get('page', 1)
    current_page_books = paginator.get_page(page)

    # Create serialized data list
    serialized_data = []
    for book in current_page_books:
        serialized_data.append({
            'id': book.id,
            'title': book.title,
            'cover_image': request.build_absolute_uri(book.cover_image.url) if book.cover_image else None
        })

    return JsonResponse(serialized_data, safe=False)


class SignupView(APIView):
    def post(self, request):
        username = request.data.get('username')

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            return Response({"message": "Thank you for your interest. We'll get back to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Thank you for your interest. You'll receive an email once the admin approves it."},
                status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_book_pages(request, book_id):
#     user = request.user
#     book = Book.objects.get(pk=book_id)
#
#     # Fetch the current_page from the request, default to 1
#     current_page = int(request.GET.get('current_page', 1))
#
#     # Calculate the end page for fetching
#     if current_page == 1:
#         # If it's an initial request, send half of the book's pages
#         end_page = book.total_pages // 5
#         start_page = 1
#     else:
#         # For subsequent requests, load the full set of pages
#         pages_requested = 10
#         start_page = current_page + 1  # Start from the page next to current
#         end_page = min(start_page + pages_requested - 1, book.total_pages)  # Fetch the next set of pages without exceeding total pages
#
#     # Fetching the images from DigitalOcean Spaces using Django's default storage
#     page_images_urls = []
#
#     for i in range(start_page, end_page + 1):
#         image_name = 'ebooks/{0}/page_{1}.jpeg'.format(book_id, i)
#         if default_storage.exists(image_name):
#             url = default_storage.url(image_name)
#             page_images_urls.append(url)
#
#     return JsonResponse({'page_images': page_images_urls})

@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "No account with this email address."}, status=status.HTTP_404_NOT_FOUND)

    code = ''.join(random.choice('0123456789') for i in range(6))
    PasswordResetCode.objects.create(user=user, code=code)

    send_mail(
        'Your password reset code',
        f'Your code is: {code}\n\nTo reset your password, click the following link:\nhttps://nasaqlibrary.org/resetPassword',
        'info@nasaqlibrary.org',
        [email],
        fail_silently=False,
    )

    print(code)
    return Response({"detail": "Reset code sent to email."}, status=status.HTTP_200_OK)

@api_view(['POST'])
def verify_password_reset(request):
    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not all([email, code, password, confirm_password]):
        return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "No account with this email address."}, status=status.HTTP_404_NOT_FOUND)

    try:
        reset_code = PasswordResetCode.objects.get(user=user, code=code)
    except PasswordResetCode.DoesNotExist:
        return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

    if reset_code.is_expired():
        reset_code.delete()
        return Response({"detail": "Code has expired."}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({"detail": "Passwords don't match."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.save()

    reset_code.delete()
    return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_pages(request, book_id):
    user = request.user
    book = Book.objects.get(pk=book_id)

    # Fetch the current_page from the request, default to 0
    current_page = int(request.GET.get('current_page', 0))
    pages_per_request = 10

    # Calculate the start and end pages for fetching
    start_page = current_page   # Start from the page next to current
    end_page = min(start_page + pages_per_request - 1, book.total_pages)  # Fetch the next set of pages without exceeding total pages

    # Fetching the images from DigitalOcean Spaces using Django's default storage
    page_images_urls = []

    for i in range(start_page, end_page + 1):
        image_name = 'ebooks/{0}/page_{1}.jpeg'.format(book_id, i)
        if default_storage.exists(image_name):
            url = default_storage.url(image_name)
            page_images_urls.append(url)

    return JsonResponse({'page_images': page_images_urls})

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_book_pages(request, book_id):
#     user = request.user
#     book = Book.objects.get(pk=book_id)
#
#
#     # Fetching the images from DigitalOcean Spaces using Django's default storage
#     page_images_urls = []
#
#     for i in range(start_page, end_page + 1):
#         image_name = 'ebooks/{0}/page_{1}.jpeg'.format(book_id, i)
#         if default_storage.exists(image_name):
#             url = default_storage.url(image_name)
#             page_images_urls.append(url)
#
#     return JsonResponse({'page_images': page_images_urls})

#
# class BookNoteView(generics.GenericAPIView):
#     serializer_class = NoteSerializer
#
#     def get(self, request, book_id, *args, **kwargs):
#         # Fetch the note for the book, assuming the user is logged in (handled by authentication)
#         note = Note.objects.filter(book_id=book_id, user=request.user).first()
#
#         # If note exists, return it, else, return empty data
#         if note:
#             return Response(self.get_serializer(note).data, status=status.HTTP_200_OK)
#         else:
#             return Response({}, status=status.HTTP_204_NO_CONTENT)
#
#     def post(self, request, book_id, *args, **kwargs):
#         # Save a new note or update the existing one
#
#         # Fetch existing note
#         note = Note.objects.filter(book_id=book_id, user=request.user).first()
#
#         # If note exists, update it
#         if note:
#             serializer = self.get_serializer(note, data=request.data, partial=True)
#         else:
#             # If no note exists, create one
#             serializer = self.get_serializer(data={**request.data, "book": book_id, "user": request.user.id})
#
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
# def convert_pdf_to_images(request, book_id, start_page, end_page):
#     book = Book.objects.get(id=book_id)
#     pdf_path = book.ebook_path.path
#     images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
#     image_bytes = []
#
#     for i, image in enumerate(images):
#         byte_io = io.BytesIO()
#         image.save(byte_io, format='PNG')
#         image_bytes.append(byte_io.getvalue())
#
#     # For now, let's return the first image as an example
#     return HttpResponse(image_bytes[0], content_type="image/png")
#
#
#
# def book_list(request):
#     search_query = request.GET.get('search', '')  # Get the search query if present
#     if search_query:
#         books = Book.objects.filter(Q(title__icontains=search_query))
#         print(books)
#         return render(request, 'ebooks/home.html', {'search_results': books})
#     else:
#         books = Book.objects.all()
#         categories = Category.objects.annotate(num_books=Count('books')).filter(num_books__gt=0)
#         return render(request, 'ebooks/home.html', {'books': books, 'categories': categories})
#
#
# class NoteForm(forms.ModelForm):
#     class Meta:
#         model = Note
#         fields = ['text']
#
#
#
# def read_book(request, book_id):
#     book = Book.objects.get(id=book_id)
#     try:
#         note = Note.objects.get(user=request.user, book=book)
#     except Note.DoesNotExist:
#         note = None
#
#     note_form = NoteForm(instance=note)
#     reviews = Review.objects.filter(book=book)
#
#     if request.method == 'POST':
#         note_form = NoteForm(request.POST, instance=note)
#         if note_form.is_valid():
#             new_note = note_form.save(commit=False)
#             new_note.user = request.user
#             new_note.book = book
#             new_note.save()
#
#     context = {
#         'pdf_url': book.ebook_path.url,
#         'book': book,
#         'note_form': note_form,
#         'reviews': reviews,
#     }
#     return render(request, 'ebooks/read_book.html', context)
