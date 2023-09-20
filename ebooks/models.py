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


def convert_single_page_to_image(book, page_num):
    """Converts a single page of the book's PDF to an image."""
    with book.ebook_path.open('rb') as pdf_file:
        images = convert_from_bytes(pdf_file.read(), first_page=page_num, last_page=page_num)

    image_name = f"page_{page_num}.jpeg"
    image_path = os.path.join('ebooks', str(book.pk), image_name)

    image_byte_array = io.BytesIO()
    images[0].save(image_byte_array, format='JPEG', quality=100)
    book.ebook_path.storage.save(image_path, ContentFile(image_byte_array.getvalue()))

    # Cleanup
    del images
    image_byte_array.close()


class Book(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    author = models.CharField(max_length=255)
    ebook_path = models.FileField(upload_to=get_file_path, null=True, blank=True)
    cover_image = models.ImageField(upload_to=get_cover_image_path, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    published_year = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorited_by = models.ManyToManyField(User, related_name="favorite_books", blank=True)
    total_pages = models.PositiveIntegerField(null=True, blank=True)

    # def save(self, *args, **kwargs):
    #     """Override the save method to handle ebook uploads."""
    #
    #     # Save the instance so it gets an ID
    #     super().save(*args, **kwargs)
    #
    #     # Convert the saved PDF to images
    #     with self.ebook_path.open('rb') as pdf_file:
    #         images = convert_from_bytes(pdf_file.read())
    #     self.total_pages = len(images)
    #     directory_path = os.path.join("ebooks", str(self.pk))
    #
    #     for idx, image in enumerate(images, start=1):
    #         image_name = os.path.join(directory_path, f"page_{idx}.jpeg")
    #         image_byte_array = io.BytesIO()
    #         image.save(image_byte_array, format='JPEG', quality=100)
    #         self.ebook_path.storage.save(image_name, ContentFile(image_byte_array.getvalue()))
    #
    #     super().save(update_fields=['total_pages'])
    def save(self, *args, **kwargs):
        # Handle cover_image
        cover_image_changed = False
        if self.cover_image and hasattr(self.cover_image, 'file'):
            # Save the instance first to get an ID for cover_image's path
            super().save(*args, **kwargs)
            cover_image_changed = True

        # Handle ebook_path
        ebook_changed = False
        if self.ebook_path:
            with self.ebook_path.open('rb') as pdf_file:
                reader = PdfReader(pdf_file)
                total_pages = len(reader.pages)

            self.total_pages = total_pages
            ebook_changed = True

        # Save the instance first if ebook changed but cover_image did not
        if ebook_changed and not cover_image_changed:
            super().save(*args, **kwargs)

        # Convert pages to images only if the ebook has changed
        if ebook_changed:
            for page_num in range(1, self.total_pages + 1):
                convert_single_page_to_image(self, page_num)

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
