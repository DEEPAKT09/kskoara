from django.contrib.auth.forms import UserCreationForm
from . models import *
from django import forms
from django.contrib.auth.models import User
from .models import Customer  # Import your custom customer model

# class CustomerUserForm(UserCreationForm):
#     first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}))
#     last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'}))
#     username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter User Name'}))
#     email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}))
#     password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Your Password'}))
#     password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Retype Your Password'}))
#     address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}))
#     mobile = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile Number'}))

#     class Meta:
#         model = Customer  # This should be User since we are dealing with user creation
#         fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'address', 'mobile']

class CustomerUserForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}))
    mobile = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile Number'}))
    address = forms.CharField(max_length=255, widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = Customer
        fields = ['email', 'mobile', 'address', 'password1', 'password2']


    def save(self, commit=True):
        # Save the User instance first
        user = super().save(commit=False)
        
        # Create Customer instance after saving the User model
        if commit:
            user.save()
            # Create Customer instance with additional fields like address and mobile
            customer = Customer.objects.create(
                user=user,
                address=self.cleaned_data['address'],
                mobile=self.cleaned_data['mobile']
            )
        return user  # Return the created user instance (can also return customer if needed)