import json
from rest_framework import status
from rest_framework.test import APITestCase
from whereithurtsapi.models import Treatment, Hurt, TreatmentType, Bodypart, Update
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

        # parse JSON from API's response
        json_response = json.loads(response.content)

        # store auth token
        self.token = json_response["token"]

        # Assert that a user was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # create treatmenttype and bodyparts to save w Treatment and Hurt
        treatmenttype = TreatmentType()
        treatmenttype.name = "test treat type"
        treatmenttype.save()

        bodypart = Bodypart()
        bodypart.name = "test part"
        bodypart.save()

        # Create a Treatment and a Hurt (and update for that hurt) that we can associated with a Healing
        treatment = Treatment()
        treatment.name = "test treat"
        treatment.added_by_id = 1
        treatment.treatmenttype_id = 1
        treatment.bodypart_id = 1
        treatment.added_by_id = 1
        treatment.added_on = timezone.now()
        treatment.notes = "no notes"
        treatment.save()

        hurt = Hurt()
        hurt.name = "test hurt"
        hurt.patient_id = 1
        hurt.bodypart_id = 1
        hurt.treatmenttype_id = 1
        hurt.added_on = timezone.now()
        hurt.save()

        update = Update()
        update.hurt_id = 1
        update.notes = "first update"
        update.pain_level = 4
        update.added_on = timezone.now()
        update.save()

    def test_create_healing_with_one_treatment_and_one_hurt(self):
        """ create a healing and make sure its tagged with one existing hurt and one existing treatment """
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [1],
            "hurt_ids": [1]
        }

        # make sure request is authenticated
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["duration"], 1000)
        self.assertEqual(json_response["notes"], "great healing!!")
        self.assertEqual(len(json_response["hurts"]), 1)
        self.assertEqual(len(json_response["treatments"]), 1)

    def test_try_to_create_healing_with_nonexisting_treatment(self):
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [2],
            "hurt_ids": [1]
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(
            json_response["message"], 'request contains a treatment id for a non-existent treatment')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


    def test_try_to_create_healing_with_nonexisting_hurt(self):
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [1],
            "hurt_ids": [2]
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(
            json_response["message"], 'request contains a hurt id for a non-existent hurt')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
