from django.urls import path

from .views import (
    EmployeeCreateView,
    EmployeeDeleteView,
    EmployeeListView,
    EmployeeUpdateView,
)

urlpatterns = [
    path("", EmployeeListView.as_view(), name="employee_list"),
    path("add/", EmployeeCreateView.as_view(), name="employee_add"),
    path("<int:pk>/edit/", EmployeeUpdateView.as_view(), name="employee_edit"),
    path(
        "<int:pk>/delete/",
        EmployeeDeleteView.as_view(),
        name="employee_delete",
    ),
]
