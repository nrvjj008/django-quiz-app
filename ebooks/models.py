from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_init
from django.dispatch import receiver
from PyPDF2 import PdfReader

from django.core.files.storage import default_storage as storage
from pdf2image import convert_from_path
from django.core.files.base import ContentFile
import io, os
from pdf2image import convert_from_bytes
from concurrent.futures import ThreadPoolExecutor
import threading
from django.db import close_old_connections
from time import sleep
from django.core.files.uploadedfile import InMemoryUploadedFile
import datetime
from django.utils import timezone
from django.core.mail import send_mail


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

def get_cover_image_path(instance, filename):
    """Determine the path for the uploaded cover image."""
    return os.path.join('book_covers', str(instance.pk), filename)

def get_file_path(instance, filename):
    """Determine the path for the uploaded ebook."""
    return os.path.join('ebooks', str(instance.pk), filename)

def convert_single_page_to_image(book, page_num, pdf_data):
    """Converts a single page of the book's PDF to an image."""
    images = convert_from_bytes(pdf_data, first_page=page_num, last_page=page_num)

    image_name = f"page_{page_num}.jpeg"
    image_path = os.path.join('ebooks', str(book.pk), image_name)

    with io.BytesIO() as image_byte_array:
        images[0].save(image_byte_array, format='JPEG', quality=100)
        book.ebook_path.storage.save(image_path, ContentFile(image_byte_array.getvalue()))

    del images


class Book(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    author = models.CharField(max_length=255)
    ebook_path = models.FileField(upload_to=get_file_path)
    cover_image = models.ImageField(upload_to=get_cover_image_path)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    published_year = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorited_by = models.ManyToManyField(User, related_name="favorite_books", blank=True)
    total_pages = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Handle cover_image
        cover_image_changed = False
        if self.cover_image and hasattr(self.cover_image, 'file'):
            super().save(*args, **kwargs)  # Save to get an ID
            cover_image_changed = True

        # Handle ebook_path
        ebook_changed = False
        pdf_data = None

        if self.ebook_path:
            pdf_data = self.ebook_path.read()
            try:
                reader = PdfReader(io.BytesIO(pdf_data))
                self.total_pages = len(reader.pages)
                ebook_changed = True
            except Exception as e:
                self.total_pages = 0

        # Convert pages to images only if the ebook has changed
        if ebook_changed and pdf_data:
            for page_num in range(1, self.total_pages + 1):
                convert_single_page_to_image(self, page_num, pdf_data)

        # Save the instance to update any changes, especially total_pages
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        total_rating = sum(review.rating for review in self.reviews.all())
        number_of_reviews = self.reviews.count()
        return round(total_rating / number_of_reviews, 2) if number_of_reviews else 0

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     if self.ebook_path:  # Make sure a file is provided
    #         if not self.page_count:  # Only calculate if it's not already set
    #             try:
    #                 print("Attempting to read PDF...")  # Debug line
    #                 with storage.open(self.ebook_path.path, 'rb') as pdf_path:
    #                     pdf = PdfFileReader(pdf_path)
    #                     self.page_count = pdf.getNumPages()
    #                     print(f"Page count set to {self.page_count}")  # Debug line
    #             except Exception as e:
    #                 print(f"An error occurred while calculating page count: {e}")
    #     super(Book, self).save(*args, **kwargs)
    #     print(f"Saved with page count {self.page_count}")  # Debug line


class UserBookProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_read_page = models.PositiveIntegerField(default=1)

class NewsletterSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscribed = models.BooleanField(default=True)

    def __str__(self):
        return self.user.email


class Newsletter(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return f"Newsletter {self.subject}"

    def send_newsletter(self):
        subscribed_users = NewsletterSubscription.objects.filter(subscribed=True)
        # Extract the email addresses correctly by accessing the related User object
        recipient_list = [sub.user.email for sub in subscribed_users if sub.user.email]
        management_link = "\n\nTo manage your subscription, visit https://nasaqlibrary.org/newsLetter"
        full_message = f"{self.message}{management_link}"

        # Send the email
        send_mail(
            subject=self.subject,
            message=full_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=recipient_list,
            fail_silently=True,
        )

        # Update the sent_at time
        self.save()

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"


class Note(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"


class Contact(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class UserReason(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reason_for_joining')
    reason = models.TextField()

    def __str__(self):
        return self.user.username



class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=30)