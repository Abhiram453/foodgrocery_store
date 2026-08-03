from django import forms
from .models import Product, Category


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
