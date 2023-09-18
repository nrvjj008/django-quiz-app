from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.html import mark_safe
from django.conf import settings


from .models import Book, Category, Review, Note, Language, Contact, UserReason
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'language', 'created_at', 'updated_at']
    search_fields = ['title', 'author']
    list_filter = ['category', 'language']
    ordering = ['created_at']
    exclude = ['favorited_by', 'total_pages']


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
    list_display = ('username', 'email', 'date_joined', 'get_reason', 'is_active', 'accept_user', 'reject_user')
    ordering = ('-date_joined',)  # LIFO ordering
    inlines = (UserReasonInline,)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:user_id>/accept/', self.accept_user_view, name='accept_user'),
            path('<path:user_id>/reject/', self.reject_user_view, name='reject_user')
        ]
        return custom_urls + urls

    def get_reason(self, obj):
        reason = UserReason.objects.filter(user=obj).first()
        return reason.reason if reason else "-"
    get_reason.short_description = 'Reason for Joining'

    def accept_user(self, obj):
        return mark_safe(f'<a href="{obj.id}/accept/" class="button">Accept</a>')
    accept_user.short_description = 'Accept'
    accept_user.allow_tags = True

    def reject_user(self, obj):
        return mark_safe(f'<a href="{obj.id}/reject/" class="button">Reject</a>')
    reject_user.short_description = 'Reject'
    reject_user.allow_tags = True

    def accept_user_view(self, request, user_id):
        user = User.objects.get(pk=user_id)
        user.is_active = True
        user.save()

        # Send an email
        send_mail(
            'Your account has been approved',
            'Congratulations! Your account has been approved.',
            settings.EMAIL_HOST_USER,  # From Email
            [user.email],
            fail_silently=False,
        )

        messages.success(request, 'User has been approved and an email has been sent.')

    def reject_user_view(self, request, user_id):
        user = User.objects.get(pk=user_id)
        user.is_active = False
        user.save()

        messages.success(request, 'User has been rejected.')
        return redirect('..')

class ContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'message', 'created_at']
    ordering = ['-created_at']  # LIFO ordering
    search_fields = ['email', 'name']




# Unregister the default User admin and register the modified one.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Book, BookAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Contact, ContactAdmin)
