from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from .models import Employee


User = get_user_model()


class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = "testpass123"
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password=self.user_password
        )

    def test_login_get_renders_template(self):
        url = reverse("login")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "registration/login.html")

    def test_login_post_success_sets_message_and_redirects(self):
        url = reverse("login")
        resp = self.client.post(url, {"username": "tester", "password": self.user_password})
        # Default LoginView redirects to settings.LOGIN_REDIRECT_URL or next
        self.assertEqual(resp.status_code, 302)
        # Check messages stored
        storage = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Login successful." in str(m) for m in storage))

    def test_logout_sets_message_and_redirects(self):
        self.client.login(username="tester", password=self.user_password)
        url = reverse("logout")
        resp = self.client.post(url, follow=True)
        # LogoutView may redirect to LOGOUT_REDIRECT_URL or to login page; follow to ensure messages collected
        self.assertEqual(resp.status_code, 200)
        storage = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Logged out." in str(m) for m in storage))


class EmployeeViewsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = "testpass123"
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password=self.user_password
        )

    def test_list_requires_login(self):
        resp = self.client.get(reverse("employee_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])  # LoginRequiredMixin

    def test_create_requires_login(self):
        resp = self.client.get(reverse("employee_add"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])  # LoginRequiredMixin

    def test_update_requires_login(self):
        emp = Employee.objects.create(
            first_name="A",
            last_name="B",
            email="a.b@example.com",
            department="IT",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.get(reverse("employee_edit", args=[emp.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])  # LoginRequiredMixin

    def test_delete_requires_login(self):
        emp = Employee.objects.create(
            first_name="A",
            last_name="B",
            email="a.b2@example.com",
            department="IT",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.get(reverse("employee_delete", args=[emp.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])  # LoginRequiredMixin


class EmployeeCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password=self.password
        )
        self.client.login(username="tester", password=self.password)

    def _valid_payload(self, **overrides):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Developer",
            "date_joined": "2024-01-01",
            "salary": "75000.50",
            "is_active": "on",  # checkbox truthy
        }
        payload.update(overrides)
        return payload

    def test_employee_list_view_paginates_and_uses_template(self):
        # Create >10 employees to test pagination
        for i in range(15):
            Employee.objects.create(
                first_name=f"F{i}",
                last_name=f"L{i}",
                email=f"e{i}@example.com",
                department="Dept",
                position="Pos",
                date_joined=date(2023, 1, 1),
                salary="1000.00",
                is_active=True,
            )
        resp = self.client.get(reverse("employee_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "employees/employee_list.html")
        self.assertIn("employees", resp.context)
        self.assertEqual(len(resp.context["employees"]), 10)  # paginate_by=10

        resp_page2 = self.client.get(reverse("employee_list") + "?page=2")
        self.assertEqual(resp_page2.status_code, 200)
        self.assertEqual(len(resp_page2.context["employees"]), 5)

    def test_employee_create_get_renders_form(self):
        resp = self.client.get(reverse("employee_add"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "employees/employee_form.html")
        self.assertIn("form", resp.context)

    def test_employee_create_post_success_redirects_and_message(self):
        resp = self.client.post(reverse("employee_add"), self._valid_payload())
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("employee_list"))
        self.assertEqual(Employee.objects.count(), 1)
        storage = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Employee added successfully." in str(m) for m in storage))

    def test_employee_create_post_invalid_shows_errors(self):
        payload = self._valid_payload(email="not-an-email")
        resp = self.client.post(reverse("employee_add"), payload)
        # stays on form
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "employees/employee_form.html")
        form = resp.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("email", form.errors)
        self.assertEqual(Employee.objects.count(), 0)

    def test_employee_create_post_duplicate_email_validation(self):
        Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="dup@example.com",
            department="Eng",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.post(reverse("employee_add"), self._valid_payload(email="dup@example.com"))
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("email", form.errors)

    def test_employee_update_get_renders_form(self):
        emp = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            department="Eng",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.get(reverse("employee_edit", args=[emp.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "employees/employee_form.html")
        self.assertIn("form", resp.context)

    def test_employee_update_post_success(self):
        emp = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            department="Eng",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.post(
            reverse("employee_edit", args=[emp.pk]),
            self._valid_payload(email="jane.new@example.com"),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("employee_list"))
        emp.refresh_from_db()
        self.assertEqual(emp.email, "jane.new@example.com")
        storage = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Employee updated successfully." in str(m) for m in storage))

    def test_employee_update_post_invalid(self):
        emp = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane2@example.com",
            department="Eng",
            position="Dev",
            date_joined=date(2023, 1, 1),
            salary="50000.00",
            is_active=True,
        )
        resp = self.client.post(
            reverse("employee_edit", args=[emp.pk]),
            self._valid_payload(email="bad"),
        )
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("email", form.errors)

    def test_employee_delete_get_confirmation_template(self):
        emp = Employee.objects.create(
            first_name="Del",
            last_name="Target",
            email="del@example.com",
            department="Ops",
            position="Staff",
            date_joined=date(2023, 1, 1),
            salary="40000.00",
            is_active=True,
        )
        resp = self.client.get(reverse("employee_delete", args=[emp.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "employees/employee_confirm_delete.html")

    def test_employee_delete_post_removes_and_redirects_with_message(self):
        emp = Employee.objects.create(
            first_name="Del",
            last_name="Target",
            email="del2@example.com",
            department="Ops",
            position="Staff",
            date_joined=date(2023, 1, 1),
            salary="40000.00",
            is_active=True,
        )
        resp = self.client.post(reverse("employee_delete", args=[emp.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("employee_list"))
        self.assertFalse(Employee.objects.filter(pk=emp.pk).exists())
        storage = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Employee deleted." in str(m) for m in storage))
