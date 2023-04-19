from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# Define a custom form for user sign up that inherits from Django's built-in UserCreationForm
class SignUpForm(UserCreationForm):
    # Add an email field to the form with a validation message
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')

    # Define the fields that should be included in the form and specify the model it relates to
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
