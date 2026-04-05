from django import forms
from .models import Receipt

class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['file']