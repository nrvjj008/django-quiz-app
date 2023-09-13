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
        books_in_category = Book.objects.filter(category=category)[:10]

        if books_in_category.exists():
            book_list = []
            for book in books_in_category:
                book_list.append({
                    'id': book.id,
                    'title': book.title,
                    'cover_image': request.build_absolute_uri(book.cover_image.url)
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
def contact_us(request):
    if request.method == 'POST':
        email = request.data['email']
        name = request.data['name']
        message = request.data['message']

        Contact.objects.create(email=email, name=name, message=message)
        return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'status': 'bad request'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_books(request, category_id):
    # Fetch the category using ID
    category_ = get_object_or_404(Category, id=category_id)

    # Get books for the fetched category
    books_in_category = Book.objects.filter(category=category_).order_by('-created_at')

    # Paginate the results
    paginator = Paginator(books_in_category, 20)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_books(request):
    query = request.GET.get('query', '')
    search_type = request.GET.get('type', 'book')

    if search_type == 'book':
        books = Book.objects.filter(title__icontains=query).order_by('-created_at')
    elif search_type == 'author':
        books = Book.objects.filter(author__name__icontains=query).order_by('-created_at')
    elif search_type == 'publisher':
        books = Book.objects.filter(publisher__name__icontains=query).order_by('-created_at')
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
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Thank you for your interest. You'll receive an email once the admin approves it."},
                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
# @login_required
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
# @login_required
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
