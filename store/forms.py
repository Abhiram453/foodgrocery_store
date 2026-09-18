from django import forms
from django.contrib.auth.models import User
from .models import Product, Category, VendorProfile, CustomerAddress


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
            name = self.cleaned_data.get('name', '')
            slug = name.lower().replace(' ', '-')
        return slug

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        if discount_price is not None:
            if discount_price <= 0:
                self.add_error('discount_price', "Sale price must be greater than zero.")
            elif price is not None and discount_price >= price:
                self.add_error('discount_price', "Sale price must be strictly lower than regular price.")
        return cleaned_data


class VendorProductForm(forms.ModelForm):
    """Product form for vendors - excludes is_featured to preserve platform curation."""
    class Meta:
        model = Product
        fields = ['category', 'name', 'slug', 'description', 'price', 'discount_price', 'stock', 'low_stock_threshold', 'image', 'unit', 'recipe_tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'recipe_tags': forms.TextInput(attrs={'placeholder': 'salad, smoothie, breakfast', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'leave blank to auto-generate'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if not slug:
            name = self.cleaned_data.get('name', '')
            from django.utils.text import slugify
            slug = slugify(name)
        return slug

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        if discount_price is not None:
            if discount_price <= 0:
                self.add_error('discount_price', "Sale price must be greater than zero.")
            elif price is not None and discount_price >= price:
                self.add_error('discount_price', "Sale price must be strictly lower than regular price.")
        return cleaned_data


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = ['label', 'full_address', 'pincode', 'city', 'state', 'phone', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Home, Office'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Flat/House No, Building, Street, Area'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit pincode'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



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
