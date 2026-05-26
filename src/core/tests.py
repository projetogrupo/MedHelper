from django.test import TestCase
from django.urls import reverse


class IndexViewTests(TestCase):
    def test_index_returns_running_message(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MedHelper is running.")
