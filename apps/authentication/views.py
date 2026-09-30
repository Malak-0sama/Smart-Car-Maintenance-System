from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import CustomerRegistrationForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    template_name = "authentication/login.html"


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect("core:dashboard")
    else:
        form = CustomerRegistrationForm()

    return render(request, "authentication/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:landing")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("authentication:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "authentication/profile.html", {"form": form})
