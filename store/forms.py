from django import forms
from django.contrib.auth.models import User
from .models import Product, Category, VendorProfile


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'slug', 'description', 'price', 'discount_price', 'stock', 'low_stock_threshold', 'image', 'unit', 'is_featured', 'recipe_tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'recipe_tags': forms.TextInput(attrs={'placeholder': 'salad, smoothie, breakfast'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if not slug:
            slug = self.instance.name.lower().replace(' ', '-')
        return slug


class VendorRegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Enter username'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Enter email address'})
    )
    password = forms.CharField(
        required=True, 
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Enter password'})
    )
    shop_name = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Enter shop name'})
    )
    shop_address = forms.CharField(
        required=True, 
        widget=forms.Textarea(attrs={'class': 'auth-input', 'rows': 3, 'placeholder': 'Enter shop address'})
    )
    pincode = forms.CharField(
        max_length=10, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Enter pincode'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email
