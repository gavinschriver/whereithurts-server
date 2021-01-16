import json
from rest_framework import status
from rest_framework.test import APITestCase
from whereithurtsapi.models import Healing, Treatment, Hurt, HealingTreatment, HurtHealing
from django.utils import timezone

class HealingTests(APITestCase):
    def setUp(self):
        """create user"""
        url = "/register"
        data = {
            "username": "testUser",
            "password": "testUserPW",
            "firstname": "testUser",
            "lastname": "testUser",
            "email": "test@user.com"
        }
        # create a request, capture response from API
        response = self.client.post(url, data, format='json')

        #parse JSON from API's response
        json_response = json.loads(response.content)

        #store auth token
        self.token = json_response["token"]

        #Assert that a user was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_healing(self):
        url = "/healings"
        data = {
            "duration": 1000,
            "added_on": timezone.now(),
            "notes": "great healing!!",
            "treatment_ids": [],
            "hurt_ids": []
        }

        #make sure request is authenticated 
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.post(url, data, format='json')
        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["duration"], 1000)
        self.assertEqual(json_response["notes"], "great healing!!")
