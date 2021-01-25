import json
from whereithurtsapi.models.HurtTreatment import HurtTreatment
from whereithurtsapi.models.Healing import Healing
from rest_framework import status
from rest_framework.test import APITestCase
from whereithurtsapi.models import Treatment, Hurt, TreatmentType, Bodypart, Update, Patient, HealingTreatment, HurtHealing
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class HealingTests(APITestCase):
    def setUp(self):
        """create user"""
        url = "/register"
        data = {
            "username": "testUser",
            "password": "testUserPW",
            "firstname": "testUser",
            "lastname": "testUser",
            "email": "test@user.com",
        }
        # create a request, capture response from API
        response = self.client.post(url, data, format='json')

        # parse JSON from API's response
        json_response = json.loads(response.content)

        # store staff auth token
        self.staff_token = json_response["token"]

        # Assert that a user was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make sure user has staff permissions
        user = User.objects.get(pk=1)
        user.is_staff = True
        user.save()

        """ create second user without is_staff for permission testing """
        secondUser = User.objects.create_user(
            username="seconduser",
            email='sconduser@second.second',
            password='seconduserpassword',
            first_name="seconduser",
            last_name="seconduser"
        )

        # store non-staff token
        self.second_users_token = Token.objects.create(user=secondUser).key

        second_patient = Patient.objects.create(
            user=secondUser
        )
        second_patient.save()

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

    def test_create_healing_with_one_treatment_and_one_hurt_as_second_user(self):
        """ create a healing and make sure its tagged with one existing hurt and one existing treatment
            healing created by non-staff user
         """
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [1],
            "hurt_ids": [1],
            "intensity": 77
        }

        # make sure request is authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["duration"], 1000)
        self.assertEqual(json_response["notes"], "great healing!!")
        self.assertEqual(json_response["intensity"], 77)
        self.assertEqual(len(json_response["hurts"]), 1)
        self.assertEqual(len(json_response["treatments"]), 1)
        self.assertEqual(json_response["intensity_score"], 80)

    def test_try_to_create_healing_with_nonexisting_treatment(self):
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [2],
            "hurt_ids": [1]
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(
            json_response["message"], 'request contains a treatment id for a non-existent treatment')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_try_to_create_healing_with_nonexisting_hurt(self):
        url = "/healings"
        data = {
            "duration": 1000,
            "notes": "great healing!!",
            "treatment_ids": [1],
            "hurt_ids": [2]
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.staff_token)
        response = self.client.post(url, data, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(
            json_response["message"], 'request contains a hurt id for a non-existent hurt')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_single_healing(self):
        """ create and get a single healing;  token is second user's token """
        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()

        url = "/healings/1"

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.get(url)

        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(json_response["duration"], 1000)
        self.assertEqual(json_response["notes"], "great healing!!")
        self.assertEqual(len(json_response["hurts"]), 1)
        self.assertEqual(len(json_response["treatments"]), 1)
        self.assertEqual(json_response["owner"], True)

    def test_get_list_of_healings_with_duration_and_count_as_staff(self):
        """ create 3 healings as non-staff user, make sure response contains a "healings" key with length of 3, total duration for both, "count" key of 2, then 
        access list as staff"""

        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()
        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()
        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()

        url = "/healings"

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.staff_token)
        response = self.client.get(url)

        json_response = json.loads(response.content)
        self.assertEqual(json_response["total_healing_time"], 3000)
        self.assertEqual(json_response["count"], 3)
        self.assertEqual(len(json_response["healings"]), 3)

    def test_try_to_access_all_healings_not_as_staff(self):
        """ try to access a list of healings without patient id as user without staff permission
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.get("/healings")
        json_response = json.loads(response.content)
        self.assertEqual(
            json_response["message"], 'only staff can access a list of healings not specified by patient id')

    def test_access_healings_by_patient_id_as_non_staff_user(self):
        # create a healing as a non-staff user and access a list of healings by patient_id querystring
        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.get("/healings?patient_id=2")

        json_response = json.loads(response.content)
        self.assertEqual(len(json_response["healings"]), 1)
        self.assertEqual(json_response["count"], 1)
        self.assertEqual(json_response["total_healing_time"], 1000)

    def test_try_to_access_healings_by_patient_id_not_as_owner_or_staff(self):
        # create a healing with staff user as patient, then have the second user try to access the list with the staff user's patient id as a query param
        staff_healing = Healing()
        staff_healing.patient_id = 1
        staff_healing.duration = 1000
        staff_healing.notes = "staff person owns this"
        staff_healing.added_on = timezone.now()
        staff_healing.save()

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.second_users_token)
        response = self.client.get("/healings?patient_id=1")
        json_response = json.loads(response.content)
        self.assertEqual(
            json_response["message"], 'only staff or the patient with this id can access this list')

    def test_access_healings_by_patient_id_as_staff(self):

        """make sure a staff member can see any patient's healings by id"""

        # create a single healing as the second user
        self.test_create_healing_with_one_treatment_and_one_hurt_as_second_user()
        
        # access the second user's healing info as staff user
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.staff_token)
        response = self.client.get("/healings?patient_id=2")
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response["healings"]), 1)
        self.assertEqual(json_response["total_healing_time"], 1000)
        self.assertEqual(json_response["count"], 1)
    
    def test_update_single_healing(self):

        """create a healing instance in the database as staff user, then send a PUT request to change its values """

        # create healing
        timestamp = timezone.now()
    
        healing = Healing()
        healing.patient_id = 1
        healing.duration = 1000
        healing.intensity = 83
        healing.notes = "really good healing very intense"
        healing.added_on = timestamp
        healing.save()

        #create a HurtHealing to associated with Healing
        hurthealing = HurtHealing()
        hurthealing.hurt_id = 1
        hurthealing.healing_id = healing.id
        hurthealing.save()

        #create a HealingTreatment to associate with Healing
        healingtreatment = HealingTreatment()
        healingtreatment.treatment_id = 1
        healingtreatment.healing_id = healing.id
        healingtreatment.save()

        # emulate a PUT request that changes all basic properties besides added_on and also 
        # removes the assocaited hurt and treatment
        data = {
            "duration": 500,
            "intensity": 47,
            "notes": "actually not so good",
            "treatment_ids": [],
            "hurt_ids": []
        }

        url = f"/healings/{healing.id}"

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.staff_token)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(url)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["duration"], 500)
        self.assertEqual(json_response["notes"], "actually not so good")
        self.assertEqual(json_response["intensity"], 47)
        self.assertEqual(json_response["intensity_score"], 50)
        self.assertEqual(len(json_response["hurts"]), 0)
        self.assertEqual(len(json_response["treatments"]), 0)


# To do:
# -- delete single Healing (check for 404)
# -- udpate single Healing

# --list of healings by patient id
# --list of healings by hurt id
