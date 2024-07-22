from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Review

class SignUpForm(UserCreationForm):
    contact_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'dob', 'password1', 'password2', 'contact_number', 'address')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'contact_number', 'address')

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 5}),
        }

class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    payment_method = forms.ChoiceField(choices=[
        ('cash_on_delivery', 'Cash on Delivery'),
        ('card', 'Credit Card')
    ], required=True)
