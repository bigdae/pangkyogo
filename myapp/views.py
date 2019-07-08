from django.shortcuts import render

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse

from myapp.models import Document
from myapp.forms import DocumentForm
from PIL import Image
import telegram
import pytesseract
import io
import os
from google.cloud import vision
from google.cloud.vision import types


def list(request):
    # Handle file upload
    my_token = '727599178:AAH_ksTAfbHK7PKt4fJq28Dj91slG3BVPXQ'
    bot = telegram.Bot(token = my_token)


    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():

            time = ""

            img = Image.open(request.FILES['docfile'])
            new_height = 1280
            new_width  = int(new_height * img.width / img.height)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            area = (0,100,600,166) 
            location = getText(img, area)

            area = (0,298,600,430)
            name = getText(img, area)
            if name == "":
                name = "unknown"

                area = (0,244,600,370)
                time = getText(img, area)

            else:
                area = (0,641,600,818)
                time = getText(img, area)

            newdoc = Document(docfile = request.FILES['docfile'], place=location)
            newdoc.save()

            bot.sendMessage(chat_id = '@pangkyogo', text='location:'+location + "\n" + "name:"+name + "\ntime:"+ time)
            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('list'))
    else:
        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    documents = Document.objects.all()

    # Render list page with the documents and the form
    return render(request, 'list.html', {'documents': documents, 'form': form})


def getText(img, area):
    text = ""
    
    # 위치 제목
    cropped_img = img.crop(area)
    #cropped_img.show()

    b = io.BytesIO()
    cropped_img.save(b, format="JPEG")
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

