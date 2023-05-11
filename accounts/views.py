from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User

from .forms import RegisterUserForm


# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegisterUserForm()
        if form.is_valid():
            input = form.cleaned_data
            newuser = User.objects.create_user(
                username=input["username"],
                first_name=input["first_name"],
                last_name=input["last_name"],
                email=input["email"],
                password=input["password"],
            )
            newuser.save()
            return HttpResponse("SUCCESSFULLY REGISTERED")
    else:
        form = RegisterUserForm()
    return render(request, "accounts/register.html", {"form": form})
