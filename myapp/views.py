from django.shortcuts import render

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse

from myapp.models import Document
from myapp.forms import DocumentForm
from PIL import Image
import telegram
import io
import os
from google.cloud import vision
from google.cloud.vision import types
import datetime


def list(request):
    # Handle file upload
    my_token = '727599178:AAH_ksTAfbHK7PKt4fJq28Dj91slG3BVPXQ'
    bot = telegram.Bot(token = my_token)


    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():

            # extract text
            time = ""
            img = Image.open(request.FILES['docfile'])
            new_height = 1280
            new_width  = int(new_height * img.width / img.height)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            area = (0,100,600,166) 
            location = getText(img, area)
            location = location.rstrip('\n')

            area = (0,298,600,430)
            name = getText(img, area).rstrip('\n')
            if name == "":
                name = "EGG"
                area = (0,244,600,370)
                time = getText(img, area).rstrip('\n')
            else:
                area = (0,641,800,818)
                time = getText(img, area).rstrip('\n')

            # time setting
            time_arr = [int(i) for i in time.split(":")]
            now_datetime = datetime.datetime.now()

            if name == "EGG":
                now_datetime = now_datetime + datetime.timedelta(minutes=45)
                now_datetime = now_datetime + datetime.timedelta(minutes=time_arr[1])
                now_datetime = now_datetime + datetime.timedelta(seconds=time_arr[2])
            else:
                now_datetime = now_datetime + datetime.timedelta(minutes=time_arr[1])
                now_datetime = now_datetime + datetime.timedelta(seconds=time_arr[2])

            
            newdoc = Document(docfile = request.FILES['docfile'], name=name, place=location, time=now_datetime)

            if len(Document.objects.filter(time__gte=datetime.datetime.now()).filter(place=location)) > 0:
                newdoc.dup = "Y"
            else:
                newdoc.dup = "N"
            newdoc.save()
            text_message = '지역:'+location + "\n" + "이름:"+name + "\n시간:"+ now_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if newdoc.dup == "N" :
                bot.sendMessage(chat_id = '@pangkyogo', text=text_message)
            # Redirect to the document list after POST
            documents = Document.objects.filter(time__gte=datetime.datetime.now()).filter(dup='N')
            form = DocumentForm() # A empty, unbound form
            return render(request, 'list.html', {'documents': documents, 'form': form, 'dup': newdoc.dup, 'text_message' : text_message})
    else:
        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    #documents = Document.objects.all()
    documents = Document.objects.filter(time__gte=datetime.datetime.now()).filter(dup='N')

    # Render list page with the documents and the form
    return render(request, 'list.html', {'documents': documents, 'form': form})


def getText(img, area):
    text = ""
    
    # 위치 제목
    cropped_img = img.crop(area)
    #cropped_img.show()

    b = io.BytesIO()
    cropped_img.save(b, format="JPEG")
    #cropped_img.show()
    img_bytes = b.getvalue()

    # Instantiates a client
    client = vision.ImageAnnotatorClient()

    image = types.Image(content=img_bytes)

    # Performs label detection on the image file
    response = client.document_text_detection(image=image)
    texts = response.text_annotations
    
    if len(texts) > 0:
        text = texts[0].description

    return text

