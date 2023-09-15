from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Book, Category, Review, Note, Language, Contact, UserReason
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserReason



class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'language', 'created_at', 'updated_at']
    search_fields = ['title', 'author']
    list_filter = ['category', 'language']
    ordering = ['created_at']
    exclude = ['favorited_by','total_pages']
    # Your other custom configurations


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    search_fields = ('book__title', 'user__username')
    list_filter = ('rating', 'created_at')


class NoteAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'created_at')
    search_fields = ('book__title', 'user__username')
    list_filter = ('created_at',)


class UserReasonInline(admin.StackedInline):
    model = UserReason
    can_delete = False
    verbose_name_plural = 'Reason for Joining'


class UserAdmin(DefaultUserAdmin):
    inlines = (UserReasonInline,)


# Unregister the default User admin and register the modified one.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Book, BookAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Contact)
