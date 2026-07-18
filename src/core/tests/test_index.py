from core.models import User
from django.test import TestCase
from django.urls import reverse


class IndexViewTests(TestCase):
    def test_index_returns_running_message(self):
        user = User.objects.create_user("tester@example.com", password="x")
        self.client.force_login(user)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agendamento")
        self.assertNotContains(response, "Novo paciente")
        self.assertNotContains(response, "Novo médico")
