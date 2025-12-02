import re

from django import forms

from .models import Employee


class EmployeeForm(forms.ModelForm):
    email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    date_joined = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = Employee
        fields = [
            "first_name",
            "last_name",
            "email",
            "department",
            "position",
            "date_joined",
            "salary",
            "is_active",
            "profile_image",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            placeholder = field.label
            widget = field.widget
            base_attrs = {"placeholder": placeholder, "class": "with-placeholder"}
            # Avoid placeholder on checkboxes; keep class for consistent styling.
            if getattr(widget, "input_type", None) == "checkbox":
                base_attrs.pop("placeholder", None)
            widget.attrs.update(base_attrs)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return email
        if not self.email_regex.match(email):
            raise forms.ValidationError("Enter a valid email.")
        return email
