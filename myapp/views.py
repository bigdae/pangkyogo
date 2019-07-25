from django.shortcuts import render

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse

from myapp.models import Document
from myapp.models import DocumentConvert
from myapp.forms import DocumentForm
from PIL import Image
import telegram
import io
import os
from google.cloud import vision
from google.cloud.vision import types
import datetime
import re
from django.core.files.storage import FileSystemStorage
import time
import pytesseract
import cv2 
import matplotlib.pyplot as plt
import numpy as np
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO

MONSTER = "MONSTER"
EGG     = "EGG"
UNKNOWN   = "UNKNOWN"
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'

def sendMessage():
    my_token = '727599178:AAH_ksTAfbHK7PKt4fJq28Dj91slG3BVPXQ'
    bot = telegram.Bot(token = my_token)
    bot.sendMessage(chat_id = '@pangkyogo', text=text_message)

def loadDocument():
    return Document.objects.all()
    #return Document.objects.filter(time_original__gte=datetime.datetime.now())#.filter(dup='N')

def resize(file):
    img = Image.open(file)
    new_height = 1280
    new_width  = int(new_height * img.width / img.height)
    resized_img = img.resize((new_width, new_height), Image.ANTIALIAS)
    resized_img.save(file)
    return resized_img

def findConvertedText(name):
    try:
      obj =  DocumentConvert.objects.get(name=name)
    except DocumentConvert.DoesNotExist: 
      return name
      
    if obj :
      return obj.name_convert
    return name

def list(request):
    form = DocumentForm()
    documents = loadDocument()
    return render(request, 'list.html', {'documents': documents, 'form': form})

def getTargetTypeByTime(img):
    img = img[270:311, 238:391]
    #plt.imshow(img)
    #plt.show()
    time = pytesseract.image_to_string(img, config='--oem 3 --psm 6 -c tessedit_char_whitelist=:0123456789')
    if time.count(":") >= 2 :
      return EGG
    return MONSTER

def extractText(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            # variable initial
            place = time = name = ""

            # time for file
            time_original = datetime.datetime.strptime(request.POST['lastmodified'], '%Y-%m-%d %H:%M:%S')
            time_calc = time_original

            # image resize and convert to opencv img
            file = request.FILES['docfile']
            img = resize(file)
            stream = BytesIO()
            img.save(stream, 'JPEG')
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)       
            _, img = cv2.threshold(img, 207, 255, 1)      
  
             # find target type by time : egg, monster
            target_type = getTargetTypeByTime(img)

            if target_type == EGG :
              img_place = img[84:160, 146:511]
              img_time = img[270:311, 238:391]

              # erode 적용
              tick= 2
              kernel = np.ones((tick, tick), np.uint8)
              img_place = cv2.erode(img_place, kernel, iterations=3) 

              #plt.imshow(img_place)
              #plt.show()

              place = pytesseract.image_to_string(img_place, config='--oem 3 --psm 3', lang='kor+eng')
              time = pytesseract.image_to_string(img_time, config='--oem 3 --psm 6 -c tessedit_char_whitelist=:0123456789')
              name = EGG
            elif target_type == MONSTER:
              img_place = img[84:163, 146:511]
              img_name = img[213:400, 128:474]
              img_time = img[697:743, 474:576]

              #plt.imshow(img_time)
              #plt.show()
              place = pytesseract.image_to_string(img_place, config='--oem 3 --psm 12', lang='kor+eng')
              time = pytesseract.image_to_string(img_time, config='--oem 3 --psm 6 -c tessedit_char_whitelist=:0123456789', lang='kor')
              name = pytesseract.image_to_string(img_name, config='--oem 3 --psm 6', lang='kor+eng') 
            else:
              name = UNKNOWN       

            place = findConvertedText(place)   
            name = findConvertedText(name)   

            # calculate minutes
            time_arr =  [int(i) for i in time.split(":")]

            if target_type == EGG:
                time_calc = time_calc + datetime.timedelta(minutes=45)
            time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
            time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
            time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])

            newdoc  = Document(docfile = request.FILES['docfile']
                            , name=name
                            , name_origin = name
                            , place=place
                            , time_original=time_original
                            , time_calc=time_calc
                            , time_text=":".join(str(e) for e in time_arr))

            # duplication check
            if len(Document.objects.filter(time_original__gte=datetime.datetime.now()).filter(place=place)) > 0:
                newdoc.dup = "Y"
            else:
                newdoc.dup = "N"

            newdoc.save()
            documents = loadDocument()
            form = DocumentForm() # A empty, unbound form
            return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})


def update(request, id):
  if request.method == 'POST':


    #update convert text
    doc = Document.objects.get(id=id)
    obj, created = DocumentConvert.objects.update_or_create(
      name = doc.name,
      defaults={ 'name_convert':request.POST['name']},
    )

    id = request.POST['id']
    name = request.POST['name'].upper()
    time_calc = Document.objects.get(id=id).time_original
    
    time_text = request.POST['time_text']
    time_arr =  [int(i) for i in time_text.split(":")]
    if name.startswith("EGG"):
      time_calc = time_calc + datetime.timedelta(minutes=45)
    time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
    time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
    time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])

    document = Document.objects.get(id=id)
    document.name = request.POST['name']
    document.place = request.POST['place']
    document.time_calc = time_calc
    document.time_text = request.POST['time_text']
    print(document.save())
    newdoc = None
  else:
    form = DocumentForm()
    newdoc = Document.objects.get(id=id)
 
  form = DocumentForm()
  documents = loadDocument()
  return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})


def delete(request, id):
  Document.objects.filter(id=id).delete()
  return HttpResponseRedirect('/myapp/')

def getText(img):
  b = io.BytesIO()
  img.save(b, format="JPEG")
  img_bytes = b.getvalue()
  client = vision.ImageAnnotatorClient()
  image = types.Image(content=img_bytes)
  response = client.document_text_detection(image=image)
  return response.full_text_annotation 

def text_within(document,x1,y1,x2,y2): 
  text=""
  for page in document.pages:
    for block in page.blocks:
      for paragraph in block.paragraphs:
        for word in paragraph.words:
          for symbol in word.symbols:
            min_x=min(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            max_x=max(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            min_y=min(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            max_y=max(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            if(min_x >= x1 and max_x <= x2 and min_y >= y1 and max_y <= y2):
              text+=symbol.text
              if(symbol.property.detected_break.type==1 or 
                symbol.property.detected_break.type==3):
                text+=' '
              if(symbol.property.detected_break.type==2):
                text+='\t'
              if(symbol.property.detected_break.type==5):
                text+='\n'
  return text    