from django.db import models

class Session(models.Model):
    employer_name = models.CharField(max_length=255)
    state_irs = models.CharField(max_length=255)
    tax_year = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.employer_name


class Receipt(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    file = models.FileField(upload_to='receipts/')
    date_of_payment = models.DateField(null=True, blank=True)
    month = models.CharField(max_length=10, blank=True)
    receipt_number = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    confidence = models.CharField(max_length=10, default='High')
    source = models.CharField(max_length=10, default='AI')
    status = models.CharField(max_length=20, default='Uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, default="AI")
    status = models.CharField(max_length=20, default="Processing")
    confidence = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.receipt_number or "Receipt"