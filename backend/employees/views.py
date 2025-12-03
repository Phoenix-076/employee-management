from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import EmployeeForm
from .models import Employee


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        messages.success(self.request, "Login successful.")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Logged out.")
        return super().dispatch(request, *args, **kwargs)


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10


class EmployeeCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")
    success_message = "Employee added successfully."


class EmployeeUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")
    success_message = "Employee updated successfully."


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = "employees/employee_confirm_delete.html"
    success_url = reverse_lazy("employee_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Employee deleted.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        # Always return the list URL with deleted flag to trigger SweetAlert
        return f"{reverse_lazy('employee_list')}?deleted=1"

# Create your views here.
