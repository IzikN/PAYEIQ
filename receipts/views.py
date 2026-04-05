import time
from django.shortcuts import render, redirect
from .models import Receipt, Session
from .ai_extractor import extract_receipt_data
from .utils import derive_month
from .pdf_utils import split_pdf_to_images
from django.http import JsonResponse
import json
from django.http import FileResponse
import os
from .excel_export import export_to_excel
from django.urls import reverse
from django.utils import timezone

def landing(request):
    return render(request, 'landing.html')

def export_excel(request):
    session = Session.objects.last()

    file_path = f"media/form_g_schedule.xlsx"
    export_to_excel(session.id, file_path)

    return FileResponse(open(file_path, 'rb'), as_attachment=True)


def dashboard(request):
    session_id = request.GET.get('session_id')
    session = None
    receipts = []

    # If a session exists in URL, load it
    if session_id:
        session = Session.objects.get(id=session_id)
        receipts = Receipt.objects.filter(session=session, status="Done").order_by('date_of_payment')

    if request.method == 'POST':
        employer_name = request.POST.get('employer_name')
        state_irs = request.POST.get('state_irs')
        tax_year = request.POST.get('tax_year')

        # Always create NEW session for new client
        session = Session.objects.create(
            employer_name=employer_name,
            state_irs=state_irs,
            tax_year=tax_year
        )

        files = request.FILES.getlist('files')
        for f in files:
            receipt = Receipt.objects.create(
                session=session,
                file=f,
                receipt_number="PROCESSING...",
                status='Extracting',
                source="AI"
            )

            file_path = receipt.file.path

            # PDF
            if file_path.lower().endswith(".pdf"):
                try:
                    image_paths = split_pdf_to_images(file_path)

                    for img_path in image_paths:
                        time.sleep(1)
                        data = extract_receipt_data(img_path)

                        Receipt.objects.create(
                            session=session,
                            file=img_path,
                            date_of_payment=data.get("date_of_payment"),
                            receipt_number=data.get("receipt_number") or "UNKNOWN",
                            amount=data.get("amount") or 0,
                            confidence=data.get("confidence"),
                            month=derive_month(data.get("date_of_payment")),
                            status="Done",
                            source="AI"
                        )

                    receipt.status = "Processed (PDF)"
                    receipt.save()

                except Exception as e:
                    receipt.status = "Error"
                    receipt.save()

            else:
                time.sleep(1)
                data = extract_receipt_data(file_path)

                receipt.date_of_payment = data.get("date_of_payment")
                receipt.receipt_number = data.get("receipt_number") or "UNKNOWN"
                receipt.amount = data.get("amount") or 0
                receipt.confidence = data.get("confidence")
                receipt.month = derive_month(data.get("date_of_payment"))
                receipt.status = "Done"
                receipt.source = "AI"
                receipt.save()

        return redirect(f"{reverse('dashboard')}?session_id={session.id}")

    return render(request, 'dashboard.html', {
        'receipts': receipts,
        'session': session
    })

def update_receipt(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        receipt_id = data.get('id')
        field = data.get('field')
        value = data.get('value')

        receipt = Receipt.objects.get(id=receipt_id)
        setattr(receipt, field, value)

        receipt.source = "Manual"
        receipt.edited = True
        receipt.edited_at = timezone.now()

        if field == "date_of_payment":
            receipt.month = derive_month(value)

        receipt.save()

        return JsonResponse({'status': 'success'})
    
    

def delete_receipt(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        receipt_id = data.get('id')

        Receipt.objects.filter(id=receipt_id).delete()

        return JsonResponse({'status': 'deleted'})