from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from .forms import RegisterUserForm


# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            input = form.cleaned_data
            newuser = User.objects.create_user(
                username=input["username"],
                first_name=input["first_name"],
                last_name=input["last_name"],
                email=input["email"],
                password=input["password"],
            )
            # query client group and add to new user
            client_group = Group.objects.get(name="client")
            newuser.groups.add(client_group)
            # set new user to be a staff member
            newuser.is_staff = True
            newuser.save()
            return redirect("choose_treatments")
    else:
        form = RegisterUserForm()
    return render(request, "accounts/register.html", {"form": form})
