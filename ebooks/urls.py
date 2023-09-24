from django.urls import path
from . import views
from .views import SignupView, request_password_reset, verify_password_reset

app_name = 'ebooks'
urlpatterns = [
    # path('', views.book_list, name='book_list'),
    #  path('read_book/<int:book_id>/', views.read_book, name='read_book'),
    # path('books/convert_pdf_to_images/<int:book_id>/<int:start_page>/<int:end_page>/', views.convert_pdf_to_images,
    #      name='convert_pdf_to_images'),
    # path('api/books/', views.book_list, name='book-list'),
    path('api/books/', views.book_list, name='book-list'),
    path('api/books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('api/contactUs/', views.contact_us, name='contact_us'),
    path('api/books/category/<int:category_id>/', views.category_books, name='category_books'),
    path('api/categories/', views.list_categories, name='list_categories'),
    path('api/book-notes/<int:book_id>/', views.save_book_note, name='book-note'),
    path('api/book-review/<int:book_id>/', views.save_book_review, name='book-review'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/books/<int:book_id>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('api/user/favorites/', views.get_favorite_books, name='get_favorite_books'),
    path('api/search/', views.search_books, name='search_books'),
    path('api/book-pages/<int:book_id>/', views.get_book_pages, name='book-pages'),
    path('api/request-password-reset/', request_password_reset, name='request-password-reset'),
    path('api/verify-password-reset/', verify_password_reset, name='verify-password-reset'),

]
