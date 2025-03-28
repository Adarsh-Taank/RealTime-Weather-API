from django.urls import path
from . import views

urlpatterns = [
    path('', views.starting_page, name = 'starting'),
    path('OpenApi', views.apiform, name = 'api'),
    path('OpenApiLogin', views.open_api_login, name = 'OpenApiLogin'),
    path('OpenApiLogin2/<int:page_id>', views.open_api_login, name = 'OpenApiLogin2'),
    path('apicall', views.api_call, name = 'api_call'),
    path('RealTimeAPI', views.real_time_api, name = 'RealTimeAPI'),
    path('RealTimeAPILogin', views.realapiform, name= 'RealTimeAPILogin'),
    path('verify_num', views.verify_num, name='verify_num'),
    path('download_file_by_city', views.download_file_by_city, name='download_file_by_city')
]