from django.shortcuts import render,redirect,HttpResponse
import requests
from .forms import ApiForm, RealApiForm
from django.contrib import messages
from django.core.paginator import Paginator
from .models import *
from django.utils import timezone
import pytz
import datetime
from datetime import timedelta, date
import xlrd
import xlwt
import os 
from twilio.rest import Client
from os.path import isfile
from xlutils.copy import copy
from django.http import JsonResponse,HttpResponse

# Create your views here.
def starting_page(request):
    return render(request, 'index.html')



def apiform(request):            #[Rendering api form from forms.py........]
    form = ApiForm()
    return render(request, 'open_api_login.html',{
        'form' : form
    })

def open_api_login(request,page_id=None):   # [Hitting the open api with /entries, getting response and passing parameters to the next function api_call().......]
    # print("page_id===>",page_id)
    # print(request.method)
    # print("here in open_api_login")

    if request.method == "POST" and page_id is not None:
        # url = "https://api.publicapis.org/"+post['name']
        url = "https://api.publicapis.org/entries"
        # print("URL:",url)
        context,status_code,all_apis,limit=api_call(request,url,page_number=page_id)
        # print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
        if limit == False:
            messages.info(request, "Time and URL hit limit exceeded.")
            return redirect(apiform)

        return render(request,'open_api.html',{
        # 'count' : fltr['count'],
        'all_apis' : all_apis,
        'page_obj' : context,
        'status' : status_code,
        })
    
    if request.method == "POST" and page_id is None:
        post = ApiForm(request.POST)
        if post.is_valid():
            post = post.cleaned_data
            # print("postcleaneddata",post)
        else:
            print("form is not valid")
        if post['name'] == 'entries':
        
            url = "https://api.publicapis.org/"+post['name']
            # url = "https://api.publicapis.org/entries"
            # print("URL:",url)
            context,status_code,all_apis,limit=api_call(request,url,page_number=page_id)
            print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
            if limit == False:
                messages.info(request, "Time and URL hit limit exceeded.")
                return redirect(apiform)
            
            return render(request,'open_api.html',{
                # 'count' : fltr['count'],
                'all_apis' : all_apis,
                'page_obj' : context,
                'status' : status_code,
                })   
        else:
            messages.info(request, "Please Enter a Correct Name")
            return redirect(apiform)
    else:
        print("in get method")

from ratelimit import limits,RateLimitException
@limits(calls=2,period=60)     # [This function won't let user hit apis if time limit exceeds...]
def check_limit():
    return

def api_call(request,url,page_number=None):      #[Filtering the records and Presenting them with pagination]

    print("here in api call")
    # print(url)
    response = requests.get(url)
    try:
        print('in try')
        check_limit()
    except RateLimitException:
        print('in except')
        # messages.info(request, "Please Enter a Correct Name")
        # context =False and all_apis ==False and status_code == 200:
        # return redirect(apiform)
        return False,200,False,False
    
    print("wwwwwwwwwwww")
    fltr = response.json()
    all_apis = []
    count = 0
    status_code = response.status_code
    for x in fltr['entries']:
        count +=1
        all_apis.append({'S_NO': count, 
                        'API': x['API'],
                        'Description' : x['Description'],
                        'Link' : x['Link']})
        
    messages.success(request,"Record Filterd Successfully!")
    # all_apis=''
    context = pages(request,all_apis,page_number)
    # print("here--->",context)
    limits =True
    return context,status_code,all_apis,limits



def pages(request,all_apis,page_number=None):            #[Setting the number of pages to be shown per page]
    # print("i am here")
    # Your existing code to fetch 'all_apis' data
    
    # Define the number of items per page
    items_per_page = 50  # You can adjust this number as needed

    # Create a Paginator object
    paginator = Paginator(all_apis, items_per_page)
    # print('paginator=====>',paginator)

    # Get the current page number from the request's GET parameters
    # page_number = request.GET.get('page')
    # page_number = request.GET.get('page')

    # print('page_number=====>',page_number)
    # Get the Page object for the current page number

    page_obj = paginator.get_page(page_number)
 

    # print('page----->',page_obj)
    # print("next_page_number---->",page_obj.next_page_number())
    context = page_obj
    # print(context)
    return context

# def real_api_login(request):
#     if request.method == 'POST':
#         post = ApiForm(request.POST)
#         if post.is_valid():
#             post = post.cleaned_data
#         else:
#             print("form is not valid")

#         # url = 'https://api.weatherapi.com/v1/current.json?key=a5028a253af040e1bad61856230510&q='+post['name'] 
#         return render(request,'real_time_api_login')

def realapiform(request):          #[Rendering realapi form from forms.py........]
    form = RealApiForm()
    return render(request, 'real_time_api_login.html',{
        'form' : form
    })


def real_time_api(request):       #[Hitting the real_time_weather api accessing and filtering the data and saving it to the Database Accordingly and presenting the data in UI]


    city_name = RealApiForm(request.POST)
    # print(city_name)
    if city_name.is_valid():
            city_name = city_name.cleaned_data
            # print("postcleaneddata",city_name)
    else:
            print("form is not valid")
    
    url = 'https://api.weatherapi.com/v1/current.json?key=a5028a253af040e1bad61856230510&q='+city_name['name']

    response = requests.get(url)

    delete_data_on_date_change(request)
    
    if response.status_code == 400:
        messages.info(request, 'Please Enter Correct City Name')
        return realapiform(request) 

    else:
        
        fltr = response.json()
        current_time=fltr['location']['localtime']
        city_n = city_name['name'].title()
        parsed_time = timecheck(current_time,city_n)

        # print(parsed_time)

        if parsed_time == False:
            try:
                update_city = city.objects.filter(name = city_name['name'].title()).update(
                                            name = fltr['location']['name'],
                                            region = fltr['location']['region'],
                                            country = fltr['location']['country'],
                                            lat = fltr['location']['lat'],
                                            lon = fltr['location']['lon'],
                                            tz_id = fltr['location']['tz_id'],
                                            localtime_epoch = fltr['location']['localtime_epoch'],
                                            localtime = fltr['location']['localtime']
                )

                query = city.objects.filter(name = city_name['name'].title())[0]
                cityid = query.id
                
                # update_weather = current_weather.objects.filter(city_id = cityid_W).update(
                #                     last_updated_epoch = fltr['current']['last_updated_epoch'],
                #                     last_updated = fltr['current']['last_updated'],
                #                     temp_c = fltr['current']['temp_c'],
                #                     temp_f = fltr['current']['temp_f'],
                #                     is_day = fltr['current']['is_day'],
                #                     condition_text = fltr['current']['condition']['text'],
                #                     condition_icon = fltr['current']['condition']['icon'],
                #                     condition_code = fltr['current']['condition']['code'],
                #                     wind_mph = fltr['current']['wind_mph'],
                #                     wind_kph = fltr['current']['wind_kph'],
                #                     wind_degree = fltr['current']['wind_degree'],
                #                     wind_dir = fltr['current']['wind_dir'],
                #                     pressure_mb = fltr['current']['pressure_mb'],
                #                     pressure_in = fltr['current']['pressure_in'],
                #                     precip_mm = fltr['current']['precip_mm'],
                #                     precip_in = fltr['current']['precip_in'],
                #                     humidity = fltr['current']['humidity'],
                #                     cloud = fltr['current']['cloud'],
                #                     feelslike_c = fltr['current']['feelslike_c'],
                #                     feelslike_f = fltr['current']['feelslike_f'],
                #                     vis_km = fltr['current']['vis_km'],
                #                     vis_miles = fltr['current']['vis_miles'],
                #                     uv = fltr['current']['uv'],
                #                     gust_mph = fltr['current']['gust_mph'],
                #                     gust_kph = fltr['current']['gust_kph'],
                #                     city_id = cityid_W
                # )
                
                current = current_weather(last_updated_epoch = fltr['current']['last_updated_epoch'],
                                        last_updated = fltr['current']['last_updated'],
                                        temp_c = fltr['current']['temp_c'],
                                        temp_f = fltr['current']['temp_f'],
                                        is_day = fltr['current']['is_day'],
                                        condition_text = fltr['current']['condition']['text'],
                                        condition_icon = fltr['current']['condition']['icon'],
                                        condition_code = fltr['current']['condition']['code'],
                                        wind_mph = fltr['current']['wind_mph'],
                                        wind_kph = fltr['current']['wind_kph'],
                                        wind_degree = fltr['current']['wind_degree'],
                                        wind_dir = fltr['current']['wind_dir'],
                                        pressure_mb = fltr['current']['pressure_mb'],
                                        pressure_in = fltr['current']['pressure_in'],
                                        precip_mm = fltr['current']['precip_mm'],
                                        precip_in = fltr['current']['precip_in'],
                                        humidity = fltr['current']['humidity'],
                                        cloud = fltr['current']['cloud'],
                                        feelslike_c = fltr['current']['feelslike_c'],
                                        feelslike_f = fltr['current']['feelslike_f'],
                                        vis_km = fltr['current']['vis_km'],
                                        vis_miles = fltr['current']['vis_miles'],
                                        uv = fltr['current']['uv'],
                                        gust_mph = fltr['current']['gust_mph'],
                                        gust_kph = fltr['current']['gust_kph'],
                                        city_id = cityid)
                current.save()

            except: 
                    pass
        else:
                    
            try:
                check = city.objects.get(name = city_name['name'].title())

                # print(check)



            except :
                location = city(name = fltr['location']['name'],
                                region = fltr['location']['region'],
                                country = fltr['location']['country'],
                                lat = fltr['location']['lat'],
                                lon = fltr['location']['lon'],
                                tz_id = fltr['location']['tz_id'],
                                localtime_epoch = fltr['location']['localtime_epoch'],
                                localtime = fltr['location']['localtime'])
                
                location.save()

                query = city.objects.filter(name = city_name['name'].title())[0]
                cityid = query.id

                current = current_weather(last_updated_epoch = fltr['current']['last_updated_epoch'],
                                        last_updated = fltr['current']['last_updated'],
                                        temp_c = fltr['current']['temp_c'],
                                        temp_f = fltr['current']['temp_f'],
                                        is_day = fltr['current']['is_day'],
                                        condition_text = fltr['current']['condition']['text'],
                                        condition_icon = fltr['current']['condition']['icon'],
                                        condition_code = fltr['current']['condition']['code'],
                                        wind_mph = fltr['current']['wind_mph'],
                                        wind_kph = fltr['current']['wind_kph'],
                                        wind_degree = fltr['current']['wind_degree'],
                                        wind_dir = fltr['current']['wind_dir'],
                                        pressure_mb = fltr['current']['pressure_mb'],
                                        pressure_in = fltr['current']['pressure_in'],
                                        precip_mm = fltr['current']['precip_mm'],
                                        precip_in = fltr['current']['precip_in'],
                                        humidity = fltr['current']['humidity'],
                                        cloud = fltr['current']['cloud'],
                                        feelslike_c = fltr['current']['feelslike_c'],
                                        feelslike_f = fltr['current']['feelslike_f'],
                                        vis_km = fltr['current']['vis_km'],
                                        vis_miles = fltr['current']['vis_miles'],
                                        uv = fltr['current']['uv'],
                                        gust_mph = fltr['current']['gust_mph'],
                                        gust_kph = fltr['current']['gust_kph'],
                                        city_id = cityid)
                current.save()

    try:
        last_update_time = fltr['current']['last_updated']
        time = str(fltr['location']['localtime']).split(' ')
        # print('view time',time)

        converted_time = time[1]
        # print('conv', converted_time)
        # print('last update',last_update_time)
        query_city = city.objects.filter(name = city_name['name'].title())[0]
        cityId = query_city.id
        weather = current_weather.objects.filter(city_id = cityId,last_updated = last_update_time)[0]
        print(weather)
        
        temp = weather.temp_c
        condtion = weather.condition_text
        wind_kph = weather.wind_kph
        humidity = weather.humidity
        wind_dir = weather.wind_dir
        
    except Exception as e:
        print('in except', e)

        pass

    return render(request, 'real_time_api.html',{
        'city_Id' : cityId,
        'city_name' : city_n,
        'current_time' : converted_time,
        'temp' : temp,
        'condition' : condtion,
        'wind_kph' : wind_kph,
        'humidity' : humidity,
        'wind_dir' : wind_dir

    })
    

def timecheck(current_time=None,city_n=None):    #[Converting Time According to the Indian Time zone for saving it in the database]
    try:
        check = city.objects.get(name = city_n)
        # check_time = check.localtime
        ist = pytz.timezone('Asia/Kolkata')
        ist_time = check.localtime.astimezone(ist)

        conv_time = str(ist_time)
        # print(conv_time)
        # print(current_time)
        flag = False 
        srt = ""
        index = [x for x in range(len(conv_time)) if conv_time[x] == ':']

        for x in range(0,index[1]):
            srt = srt+conv_time[x]

        if srt == current_time:
            flag = True
        else:
            flag = False
    except:
        flag = True
    
    # print(flag)
    # print(current_time)
    # print(srt)
    return flag

def delete_data_on_date_change(request):        #[Deleting Data of Previous date and only retaining the data of previous 5 days in the Database]
    try:
        current_date = (datetime.date.today())
        previous_date = current_date - timedelta(days=5)

        current_weather.objects.filter(last_updated__lt=previous_date).delete()

    except:
        pass    


    return True



def export_data_to_excel():           #[Converting Data which have to be deleted in the above function]
    # Export city data to Excel
    city_data = city.objects.all().values()
    today = date.today()
    city_excel_file = f"C:\\Users\\Adarsh\\Documents\\New folder\\city_data_{today}.xls"
    city_headers = list(city_data.first().keys())
    existing_data = None
    city_workbook = None

    if os.path.isfile(city_excel_file):
        # If the file exists, open it for appending
        existing_data = xlrd.open_workbook(city_excel_file, formatting_info=True)
        city_workbook = copy(existing_data)

    if city_workbook is None:
        # If there is no existing workbook, create a new one
        city_workbook = xlwt.Workbook()

    if existing_data and existing_data.sheets():
        # Open the first sheet if there are existing sheets
        city_sheet = city_workbook.get_sheet(0)
        last_row = max([s.nrows for s in existing_data.sheets()])
        headers_written = True
    else:
        # If there are no existing sheets, create a new sheet
        city_sheet = city_workbook.add_sheet('City Data')
        last_row = 0
        headers_written = False

    # Write headers to the sheet only if the sheet is created
    if not headers_written:
        for col, header in enumerate(city_headers):
            city_sheet.write(last_row, col, header)

    # Write data to the sheet
    for row, data in enumerate(city_data, start=1):
        for col, header in enumerate(city_headers):
            city_sheet.write(last_row + row, col, data[header])

    # Save the workbook with appended data
    city_workbook.save(city_excel_file)

    # Export current_weather data to Excel
    weather_data = current_weather.objects.all().values()
    weather_excel_file = f"C:\\Users\\Adarsh\\Documents\\New folder\\weather_data_{today}.xls"
    weather_headers = list(weather_data.first().keys())
    existing_data = None
    weather_workbook = None

    if os.path.isfile(weather_excel_file):
        existing_data = xlrd.open_workbook(weather_excel_file, formatting_info=True)
        weather_workbook = copy(existing_data)

    if weather_workbook is None:
        # If there is no existing workbook, create a new one
        weather_workbook = xlwt.Workbook()

    if existing_data and existing_data.sheets():
        # Open the first sheet if there are existing sheets
        weather_sheet = weather_workbook.get_sheet(0)
        last_row = max([s.nrows for s in existing_data.sheets()])
        headers_written = True
    else:
        # If there are no existing sheets, create a new sheet
        weather_sheet = weather_workbook.add_sheet('Weather Data')
        last_row = 0
        headers_written = False

    # Write headers to the sheet only if the sheet is created
    if not headers_written:
        for col, header in enumerate(weather_headers):
            weather_sheet.write(last_row, col, header)

    # Write data to the sheet
    for row, data in enumerate(weather_data, start=1):
        for col, header in enumerate(weather_headers):
            weather_sheet.write(last_row + row, col, data[header])

    # Save the workbook with appended data
    weather_workbook.save(weather_excel_file)

    print('Data appended to Excel files:')


path = None
def verify_num(request):        #[Verifing Mobile Number With OPT verification from Twilio and generating the excel of the data for the particular city]
    print("in verify_num")
    if request.method == 'POST':
        num = request.POST.get('mobile')
        account_sid = "AC89ec567ceae6a51586e23fc8251cf7ef"
        auth_token = "1cb2683e3abca8c2601261d0038ab9bd"
        verify_sid = "VA98ebe787f548c94037806098f5d2f8ab"
        verified_number = "+917000337448"

        client = Client(account_sid, auth_token)

        print("here in verify_num",num)
        if num is not None:
            verification = client.verify.v2.services(verify_sid) \
            .verifications \
            .create(to=verified_number, channel="sms")
            print(verification.status)
            flag = False

        else:


            # otp = str(1234)
            otp_u = request.POST.get('ent_otp') 
            print('Entered otp => ',otp_u)
            otp_code = otp_u

            verification_check = client.verify.v2.services(verify_sid) \
            .verification_checks \
            .create(to=verified_number, code=otp_code)
            status = verification_check.status
            print(verification_check.status)

            # if otp_u == otp:
            if status == 'approved':
                flag = True
                print('otp verified')

                city_name = request.POST.get('city')
                time = request.POST.get('time')
                city_Id = request.POST.get('city_Id')
                today = date.today()
                print('city name => ',city_name)
                print('time =>',time)
                time_new=time.replace(':','-')
                print('time_new',time_new)
                print('city id ==>', city_Id)

                weather_data = current_weather.objects.filter(city_id = city_Id).values()
                # print('weather data ==>',weather_data )
                # weather_excel_file = "C:\\Users\\Adarsh\\Documents\\New folder\\"+city_name+time+"_Data.xls"
                weather_excel_file = f"C:\\Users\\Adarsh\\Documents\\New folder\\{city_name}_{today}_{time_new}_Data.xls"
                global path
                path = weather_excel_file
                
                print('excel file',weather_excel_file)
                weather_headers = list(weather_data.first().keys())
                existing_data = None
                weather_workbook = None

                if os.path.isfile(weather_excel_file):
                    existing_data = xlrd.open_workbook(weather_excel_file, formatting_info=True)
                    weather_workbook = copy(existing_data)

                if weather_workbook is None:
                    # If there is no existing workbook, create a new one
                    weather_workbook = xlwt.Workbook()

                if existing_data and existing_data.sheets():
                    # Open the first sheet if there are existing sheets
                    weather_sheet = weather_workbook.get_sheet(0)
                    last_row = max([s.nrows for s in existing_data.sheets()])
                    headers_written = True
                else:
                    # If there are no existing sheets, create a new sheet
                    weather_sheet = weather_workbook.add_sheet('Weather Data')
                    last_row = 0
                    headers_written = False

                # Write headers to the sheet only if the sheet is created
                if not headers_written:
                    for col, header in enumerate(weather_headers):
                        weather_sheet.write(last_row, col, header)

                # Write data to the sheet
                for row, data in enumerate(weather_data, start=1):
                    for col, header in enumerate(weather_headers):
                        weather_sheet.write(last_row + row, col, data[header])

                # Save the workbook with appended data
                weather_workbook.save(weather_excel_file)
                return JsonResponse({'check_otp': flag,
                            'path': weather_excel_file})
        
            else:
                flag = False
                print('otp not verified')

    return JsonResponse({'check_otp': flag})


def download_file_by_city(request):  #[This Function Let the user Download the File which is generated in the above function]
#   print('here above file_path')
  global path
  file_path = path
#   print('file path =>', file_path)

  if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            print('file response')
            return response
  else:
        return HttpResponse("File not found", status=404)
  















# def export_data_to_excel():
#     # Export city data to Excel
#     city_data = city.objects.all().values()
#     city_excel_file = 'C:\\Users\\Adarsh\\Documents\\New folder\\city_data.xls'
#     city_headers = list(city_data.first().keys())
#     existing_data = None
#     city_workbook = None

#     if os.path.isfile(city_excel_file):
#         # If the file exists, open it for appending
#         existing_data = xlrd.open_workbook(city_excel_file, formatting_info=True)
#         city_workbook = copy(existing_data)

#     if city_workbook is None:
#         # If there is no existing workbook, create a new one
#         city_workbook = xlwt.Workbook()

#     if existing_data and existing_data.sheets():
#         # Open the first sheet if there are existing sheets
#         city_sheet = city_workbook.get_sheet(0)
#         last_row = max([s.nrows for s in existing_data.sheets()])
#     else:
#         # If there are no existing sheets, create a new sheet
#         city_sheet = city_workbook.add_sheet('City Data')
#         last_row = 0

#     # Write data to the sheet
#     for row, data in enumerate(city_data, start=1):
#         for col, header in enumerate(city_headers):
#             city_sheet.write(last_row + row, col, data[header])

#     # Save the workbook with appended data
#     city_workbook.save(city_excel_file)

#     # Export current_weather data to Excel
#     weather_data = current_weather.objects.all().values()
#     weather_excel_file = 'C:\\Users\\Adarsh\\Documents\\New folder\\weather_data.xls'
#     weather_headers = list(weather_data.first().keys())
#     existing_data = None
#     weather_workbook = None

#     if os.path.isfile(weather_excel_file):
#         existing_data = xlrd.open_workbook(weather_excel_file, formatting_info=True)
#         weather_workbook = copy(existing_data)

#     if weather_workbook is None:
#         # If there is no existing workbook, create a new one
#         weather_workbook = xlwt.Workbook()

#     if existing_data and existing_data.sheets():
#         # Open the first sheet if there are existing sheets
#         weather_sheet = weather_workbook.get_sheet(0)
#         last_row = max([s.nrows for s in existing_data.sheets()])
#     else:
#         # If there are no existing sheets, create a new sheet
#         weather_sheet = weather_workbook.add_sheet('Weather Data')
#         last_row = 0

#     # Write data to the sheet
#     for row, data in enumerate(weather_data, start=1):
#         for col, header in enumerate(weather_headers):
#             weather_sheet.write(last_row + row, col, data[header])

#     # Save the workbook with appended data
#     weather_workbook.save(weather_excel_file)

#     print('Data appended to Excel files:')
