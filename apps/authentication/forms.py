from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomerRegistrationForm(UserCreationForm):
    """Public registration form. Always creates a CUSTOMER-role account —
    staff roles (Admin/Manager/Technician) are provisioned separately
    via the Django admin to prevent privilege escalation at signup."""

    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "phone_number", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.CUSTOMER
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["email", "phone_number", "first_name", "last_name"]
