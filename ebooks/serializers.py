from rest_framework import serializers
from .models import Book, Review, Note,  UserReason, UserBookProgress
from django.contrib.auth.models import User


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['comment', 'rating', 'username']

    def get_username(self, obj):
        return obj.user.username

class UserNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['text']

class BookDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True)
    user_note = serializers.SerializerMethodField()  # Change from 'notes'
    ebook_path = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    language_title = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'description', 'author', 'ebook_path', 'cover_image',
            'category', 'category_name', 'language', 'language_title', 'published_year',
            'publisher', 'reviews', 'user_note', 'average_rating','user_progress'  # Change 'notes' to 'user_note'
        ]

    def get_ebook_path(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.ebook_path.url)

    def get_language_title(self, obj):
        return obj.language.name if obj.language else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_user_note(self, obj):
        user = self.context['request'].user
        note = Note.objects.filter(user=user, book=obj).first()
        if note:
            return UserNoteSerializer(note).data['text']
        return None  # Return None if there's no note for the authenticated user

    def get_user_progress(self, obj):
        user = self.context['request'].user
        progress = UserBookProgress.objects.filter(user=user, book=obj).first()
        if progress:
            return progress.last_read_page
        return 1  # Return 1 if there's no progress for the authenticated user


class SignupSerializer(serializers.ModelSerializer):
    reason = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'reason')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        reason = validated_data.pop('reason')
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            is_active=False
        )
        user.set_password(validated_data['password'])
        user.save()

        UserReason.objects.create(user=user, reason=reason)

        return user