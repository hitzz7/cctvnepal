from django import forms
from .models import StartaProject

class ContactForm(forms.ModelForm):
    class Meta:
        model = StartaProject
        fields = ['name', 'email', 'mobile', 'description']
