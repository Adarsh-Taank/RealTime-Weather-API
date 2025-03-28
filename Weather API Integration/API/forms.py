from django import forms

class ApiForm(forms.Form):
    name = forms.CharField()

class RealApiForm(forms.Form):
    name = forms.CharField(label='Please Enter City Name')