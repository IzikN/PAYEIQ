import time
import json
import os
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.urls import reverse
from django.utils import timezone
from .models import Receipt, Session
from .ai_extractor import extract_receipt_data
from .utils import derive_month
from .pdf_utils import split_pdf_to_images
from .excel_export import export_to_excel

def landing(request):
    return render(request, 'landing.html')


def export_excel(request):
    # Fetch session ID and user name bound to this browser session
    session_id = request.session.get("session_id")
    user_name = request.session.get("user_name")

    if not session_id:
        raise Http404("No active session found for export.")

    # Retrieve exact session tied to user session ID
    session = get_object_or_404(Session, id=session_id)

    # Sanitize names for path-safe file generation
    safe_user_name = re.sub(r'[^a-zA-Z0-9_-]', '_', (user_name or "user").lower())
    safe_employer = re.sub(r'[^a-zA-Z0-9_-]', '_', session.employer_name.lower())
    
    file_path = f"media/exports/{safe_employer}_{safe_user_name}_session_{session.id}_form_g.xlsx"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    export_to_excel(session.id, file_path)

    # Provide dynamic filename for the user download
    download_filename = f"{safe_employer}_Form_G_{session.tax_year}.xlsx"
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=download_filename)

STATE_IRS_CHOICES = [
    "Abia State Internal Revenue Service",
    "Adamawa State Internal Revenue Service",
    "Akwa Ibom State Internal Revenue Service",
    "Anambra State Internal Revenue Service",
    "Bauchi State Internal Revenue Service",
    "Bayelsa State Internal Revenue Service",
    "Benue State Internal Revenue Service",
    "Borno State Internal Revenue Service",
    "Cross River State Internal Revenue Service",
    "Delta State Internal Revenue Service",
    "Ebonyi State Internal Revenue Service",
    "Edo State Internal Revenue Service",
    "Ekiti State Internal Revenue Service",
    "Enugu State Internal Revenue Service",
    "FCT Internal Revenue Service (Abuja)",
    "Gombe State Internal Revenue Service",
    "Imo State Internal Revenue Service",
    "Jigawa State Internal Revenue Service",
    "Kaduna State Internal Revenue Service",
    "Kano State Internal Revenue Service",
    "Katsina State Internal Revenue Service",
    "Kebbi State Internal Revenue Service",
    "Kogi State Internal Revenue Service",
    "Kwara State Internal Revenue Service",
    "Lagos State Internal Revenue Service",
    "Nasarawa State Internal Revenue Service",
    "Niger State Internal Revenue Service",
    "Ogun State Internal Revenue Service",
    "Ondo State Internal Revenue Service",
    "Osun State Internal Revenue Service",
    "Oyo State Internal Revenue Service",
    "Plateau State Internal Revenue Service",
    "Rivers State Internal Revenue Service",
    "Sokoto State Internal Revenue Service",
    "Taraba State Internal Revenue Service",
    "Yobe State Internal Revenue Service",
    "Zamfara State Internal Revenue Service",
]


def dashboard(request):
    session_id = request.session.get("session_id")
    user_name = request.session.get("user_name")
    session = None
    receipts = []

    # Fetch active session and its processed receipts
    if session_id:
        session = Session.objects.filter(id=session_id).first()
        if session:
            receipts = Receipt.objects.filter(
                session=session,
                status="Done"
            ).order_by('date_of_payment')

    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        employer_name = request.POST.get('employer_name')
        state_irs = request.POST.get('state_irs')
        tax_year = request.POST.get('tax_year')

        # Persist user context across multi-page actions
        if user_name:
            request.session["user_name"] = user_name

        # Create or update session record
        if session:
            session.employer_name = employer_name
            session.state_irs = state_irs
            session.tax_year = tax_year
            session.save()
        else:
            session = Session.objects.create(
                employer_name=employer_name,
                state_irs=state_irs,
                tax_year=tax_year
            )
            request.session["session_id"] = session.id

        # Handle uploaded receipts
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

            # PDF Handling: Split into page images first
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

                except Exception:
                    receipt.status = "Error"
                    receipt.save()

            # Image Handling: Extract directly
            else:
                try:
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
                except Exception:
                    receipt.status = "Error"
                    receipt.save()

        return redirect(reverse('dashboard'))

    # Context supplied to template GET requests
    context = {
        'session': session,
        'receipts': receipts,
        'user_name': user_name,
        'state_irs_list': STATE_IRS_CHOICES,
    }

    return render(request, 'dashboard.html', context)


def update_receipt(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = request.session.get("session_id")

        if not session_id:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

        receipt_id = data.get('id')
        field = data.get('field')
        value = data.get('value')

        # Scope receipt update to the active session ID
        receipt = get_object_or_404(Receipt, id=receipt_id, session_id=session_id)
        
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
        session_id = request.session.get("session_id")
        receipt_id = data.get('id')

        if not session_id:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

        # Ensure receipt deletion is strictly locked to the user's active session
        Receipt.objects.filter(id=receipt_id, session_id=session_id).delete()

        return JsonResponse({'status': 'deleted'})

def setup(request):
    """Handles initial user identification and creates a fresh session context."""
    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        employer_name = request.POST.get('employer_name')

        # Store user details in session cookie for tenant isolation
        request.session['user_name'] = user_name
        request.session['employer_name'] = employer_name

        # Clear any prior active session ID so a fresh one starts on dashboard
        if 'session_id' in request.session:
            del request.session['session_id']

        return redirect(reverse('dashboard'))

    return render(request, 'setup.html')


def new_session(request):
    """Resets active session and redirects back to setup for a new client."""
    request.session.flush()  # Clears all session keys cleanly
    return redirect(reverse('setup'))

