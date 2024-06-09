
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseForbidden, FileResponse
from django import forms
from django.db import models
from django.urls import reverse
import datetime
import json
from io import BytesIO
from django.http import FileResponse 
from reportlab.pdfgen import canvas
from django.core.mail import send_mail
from django.conf import settings
import time
import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.pdfgen import canvas
# Create your views here.
class DateInput(forms.DateInput):
    input_type = 'date'
class TimeInput(forms.TimeInput):
    input_type = 'time'
class reserv(forms.Form):
    name = forms.CharField(label="Please enter your name", widget=forms.TextInput(attrs={'class': 'name'}))
    lastname = forms.CharField(label="Please enter your last name", widget=forms.TextInput(attrs={'class': 'lastname'}))
    email = forms.EmailField(label="Please enter your email address", widget=forms.EmailInput(attrs={'class': 'email'}))
    phonenumber = forms.CharField(label="Please enter your phone number", widget=forms.TextInput(attrs={'class': 'phonenumber'}))
    guestchoices = [ 
        ('1',1),
        ('2',2),
        ('3',3),
        ('4',4),
        ('5',5),
        ('6',6),
        ('7',7),
        ('8',8),
        ('9',9),
        ('10',10),
    ]
    guests = forms.ChoiceField(label="Table for", choices=guestchoices, widget=forms.Select(attrs={'class': 'guests'}))
    date = forms.DateField(label='Select a date', widget=DateInput(attrs={'class': 'date'}))
    time = forms.TimeField(label="What time will your visit be", widget=TimeInput(attrs={'class': 'time'}))
class log_in_form(forms.Form):
    usr = forms.CharField(label="Please enter your username", widget=forms.TextInput({'class': 'usr'}))
    password = forms.CharField(label="Please enter password", widget=forms.PasswordInput({'class': 'password'}))


class Reservations(models.Model):
    name = models.CharField(max_length=64)
    lastname = models.CharField(max_length=64)
    email = models.EmailField(max_length=64)
    phonenumber = models.CharField(max_length=11, null=True)
    guests = models.IntegerField(null=True)
    datee = models.DateField(max_length=10, null=True)
    time =  models.TimeField(null=True)
    confirmed = models.CharField(default="Not Confirmed", max_length=3)
    submission_time = models.TimeField(null=True)
    target1_time = models.TimeField(null=True)

class date_picker(forms.Form):
    date = forms.DateField(label='Fetch reservations for ', widget=DateInput(attrs={'class': 'date'}))
###########################################################################################################################################   
def reservation(request):
    if request.method == "POST":
        form = reserv(request.POST)
        if form.is_valid():
            request.session['name'] = form.cleaned_data['name']
            request.session['lastname'] = form.cleaned_data['lastname']
            request.session['email'] = form.cleaned_data['email']
            request.session['date'] =  form.cleaned_data['date'].isoformat()
            request.session['phonenumber'] = form.cleaned_data['phonenumber']
            request.session['guests']= form.cleaned_data['guests']
            request.session['time'] = form.cleaned_data['time'].isoformat()
    return render(request,"reservation.html", {"form": reserv})
###########################################################################################################################################
def checkavailability(request):
    name = request.session.get('name')
    time = request.session.get('time')
    date = request.session.get('date')
    lastname = request.session.get('lastname')
    email = request.session.get('email')
    guests = request.session.get('guests')
    phonenumber = request.session.get('phonenumber')
    ######################################CHECK_AVAILABILITY################################################################################
    target_time = datetime.datetime.strptime(time, "%H:%M:%S")
    conflictual_reservations = Reservations.objects.filter(datee= date, target1_time=target_time.replace(minute=00))
    ########################################################################################################################################
    ###################################### ANTI-SPAMMING PROTECTION ########################################################################
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    time_today = datetime.datetime.now().time().strftime("%H:%M")
    if date < today:
        return JsonResponse({"msg": "Invalid"})
    existing_future_reservations = Reservations.objects.filter(email= email, confirmed="Not Confirmed")
    if date == today and time <= time_today:
        return JsonResponse({"msg": "Invalid"})
    if len(existing_future_reservations) > 0:
        return JsonResponse({"msg": "unfulfilled reservation"})
    #########################################################################################################################################
    if name == None:
        return JsonResponse({"msg": "New Session"})
    if len(conflictual_reservations )< 20 and len(existing_future_reservations) == 0:
        requesttime = datetime.datetime.now()
        confirmed_reservation = Reservations(name=name, lastname= lastname, datee=date,target1_time= target_time.replace(minute=00),  email=email, guests=guests, phonenumber= phonenumber, submission_time=requesttime, time=time )
        confirmed_reservation.save()
        # Email setup
        smtp_server = "smtp.gmail.com"
        port = 465  # For SSL
        sender_email = "confirmation.lakeplaza@gmail.com"
        receiver_email = email
        password = "nxkqspjxogbyvwsj"
        subject = "Welcome to Lake Plaza"

        # HTML content for the email
        html_content = """
        <html>
            <body>
                <h1>Reservation Received, {name}</h1>
                <p>Hello {name},</p>
                <p>We received your reservation here at Bruxie's </p>
                <p>Best regards,<br>Lake Plaza Team</p>
            </body>
        </html>
        """.format(name=name)

# Create a multipart message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Attach the HTML content to the multipart message
        mime_text = MIMEText(html_content, "html")
        message.attach(mime_text)  # Correct attachment to multipart message

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Send the email with SSL connection
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            #server.sendmail(sender_email, receiver_email, message.as_string())
        return JsonResponse({"msg": "Available"})
    if len(conflictual_reservations) >= 20:
        return JsonResponse({"msg": "Not Available"})

def admin(request):
    my_model = Reservations.objects.all()
    date_input = date_picker
    if request.session.get('usr') is None and request.session.get('password') is None:
            return HttpResponseRedirect("https://reserv-bruxies.onrender.com/bruxies/authn")
    else:
        return render(request, "admin.html", {"Reservations": my_model, "date_input": date_input })
    

def authn(request):
    form = log_in_form(request.POST)
    if request.method == "POST":
        if form.is_valid():
            usr  = form.cleaned_data['usr']
            password = form.cleaned_data['password']
            request.session['usr'] = usr
            request.session['password'] = password
            if usr == "Mourad":
                return HttpResponseRedirect("https://reserv-bruxies.onrender.com/bruxies/admin")
            else :
                return HttpResponseForbidden("We Know what you're trying to do ;)")
    else :
        return render(request, "authn.html", {"form": form} )



def home(request): 
    return render(request, "fada2y.html")
    
def confirm_reservation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        if "id" not in data or "msg" not in data:
            return JsonResponse({"msg": "Invalid data"}, status=400)
        
        if data["msg"] == "Confirmed":
            reservation_id = data["id"]
            try:
                reservation = Reservations.objects.get(id=reservation_id)
                reservation.confirmed = "Confirmed"
                reservation_email = reservation.email
                reservation.save() 
                return JsonResponse({"msg": "Confirmed"})

            except Reservations.DoesNotExist:
                return JsonResponse({"msg": "Reservation not found"}, status=404)
        else:
            return JsonResponse({"msg": "Not Confirmed"})
            
import logging

logger = logging.getLogger(__name__)
def generate_report(request):
    if request.method == "POST":
        data = json.loads(request.body)
        date_str = data["date"]
        # Parse the date string into a datetime object and store the string representation in the session
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        request.session["date"] = date_obj.strftime("%Y-%m-%d")
        return JsonResponse({"status": "Date set in session"})

    # Retrieve the date from the session and convert it back to a datetime object
    date_str = request.session.get("date")
    if date_str:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        # Query the model using the date
        my_model = Reservations.objects.filter(datee=date)
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawImage("bruxies/assets/bruxies.ico", 500, 780, width=120, preserveAspectRatio=True, mask='auto')
        p.setFont("Helvetica", 30)
        p.drawString(5, 800, f'Confirmed Reservations on {date.strftime("%d-%m-%Y")}')
        p.setFont("Helvetica", 15)
        p.setAuthor("The CyberTechts - RESERV+")
        p.setTitle(f"Confirmed Reservations on {date.strftime('%d-%m-%Y')}")
        p.setCreator("RESERV+ build98238021gh")
        p.setProducer("The CyberTechts Generate Module")

        # Iterate over the queryset and draw text for each object
        reservations_per_date = 0
        total_guests = 0
        y_position = 700
        for reservation in my_model:
            string = f'{reservation.id} | {reservation.name} | {reservation.lastname} | {reservation.time} | {reservation.email} | {reservation.guests}'
            p.drawString(100, y_position, string)
            y_position -= 20
            reservations_per_date += 1 
            total_guests += int(reservation.guests)
        p.setFont("Helvetica", 10)
        p.drawString(200, 5, f'Total Guests : {total_guests} | Total Reservations : {reservations_per_date}')
        now = datetime.datetime.now()
        p.setFont("Helvetica", 8)
        p.drawString(400, 5, f'Document generated on {now.strftime("%d-%m-%Y")}')

        p.showPage()
        p.save()
        buffer.seek(0)
        request.session["date"] = None
        return FileResponse(buffer, as_attachment=True, filename=f'{date_str} report.pdf')

    else:
        return JsonResponse({"error": "Date not found in session"}, status=400)
