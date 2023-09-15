import os
from django.core.files.storage import default_storage
from django.conf import settings
from ebooks.models import Book


def download_all_pdfs():
    # Ensure the ebooks directory exists
    ebooks_directory = os.path.join(settings.BASE_DIR, 'ebooks')
    if not os.path.exists(ebooks_directory):
        os.makedirs(ebooks_directory)

    # Fetch all books
    books = Book.objects.all()

    for book in books:
        pdf_name = 'ebooks/{0}/{1}.pdf'.format(book.id, book.title)

        # Check if the PDF exists in the storage
        if default_storage.exists(pdf_name):
            # Create directory for the book if it doesn't exist
            book_directory = os.path.join(ebooks_directory, str(book.id))
            if not os.path.exists(book_directory):
                os.makedirs(book_directory)

            # Get the PDF content from storage
            pdf_content = default_storage.open(pdf_name).read()

            # Save the PDF to the local directory
            with open(os.path.join(book_directory, '{0}.pdf'.format(book.title)), 'wb') as local_pdf:
                local_pdf.write(pdf_content)

    print('Download complete')


# If the script is run directly, execute the function
if __name__ == '__main__':
    download_all_pdfs()
