from django.core.exceptions import ValidationError
from django.views.generic.base import View
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Hurt, Patient, Update, HurtTreatment, Treatment, TreatmentLink, Bodypart, Healing
from django.utils import timezone
from itertools import chain
from operator import attrgetter
from django.db.models import Max

# Serializers


class UpdateSerializer(ModelSerializer):
    class Meta:
        model = Update
        fields = ('id', 'added_on', 'notes', 'pain_level',
                  'is_first_update', 'date_added')


class TreatmentLinkSerializer(ModelSerializer):
    class Meta:
        model = TreatmentLink
        fields = ('id', 'linktext', 'linkurl')


class HealingSerializer(ModelSerializer):
    class Meta:
        model = Healing
        fields = ('id', 'date_added', 'added_on')


class TreatmentSerializer(ModelSerializer):
    links = TreatmentLinkSerializer(many=True)
    """ JSON serializer for Treatments to embed on Hurts """
    class Meta:
        model = Treatment
        fields = ('id', 'name', 'added_on', 'added_by',
                  'notes', 'public', 'links')


class HurtSerializer(ModelSerializer):
    """JSON serializer for the Hurt model"""
    healings = HealingSerializer(many=True)
    treatments = TreatmentSerializer(many=True)
    updates = UpdateSerializer(many=True)

    class Meta:
        model = Hurt
        fields = ('id', 'patient', 'healings', 'date_added', 'bodypart', 'name', 'added_on', 'is_active', 'notes', 'pain_level',
                  'healing_count', 'treatments', 'updates', 'last_update', 'first_update_id', 'owner', 'latest_pain_level')
        depth = 1

# Viewset


class HurtViewSet(ViewSet):
    def retrieve(self, request, pk=None):
        """ Access a single Hurt """
        try:
            hurt = Hurt.objects.get(pk=pk)
        except Hurt.DoesNotExist:
            return Response({'message': 'hurt does not exist'}, status=status.HTTP_404_NOT_FOUND)

        hurt.owner = False

        if hurt.patient == Patient.objects.get(user=request.auth.user):
            hurt.owner = True

        serializer = HurtSerializer(hurt, context={'request': request})
        hurt_data = serializer.data

        # serialize matching Healings for this Hurt into list of dicts, then add type

        healings = Healing.objects.filter(hurt_healings__hurt=hurt)
        healings_list = HealingSerializer(healings, many=True).data
        for healing in healings_list:
            healing.update({"history_type": "Healing"})

        # serialize matching updates. Add a type, and also a Created if it was the first update
        updates = hurt.update_set.all()
        updates_list = UpdateSerializer(updates, many=True).data
        for update in updates_list:
            if update["is_first_update"]:
                update.update({"history_type": "Created on"})
            else:
                update.update({"history_type": "Update"})

        # combine the two lists into one called history
        history = healings_list + updates_list

        # history is returned with newest first by default; check for q string to see if this is flipped with "oldest"
        order = self.request.query_params.get("order_history", None)

        reverse = True
        if order is not None:
            if order == "oldest":
                reverse = False

        # sorting function to compare by datetime value of "added_on"
        def by_date(row): return row["added_on"]

        history = sorted(history, key=by_date, reverse=reverse)

        # add the history list as a k/v pair to the serialzied Hurt dict
        hurt_data["history"] = history

        return Response(hurt_data, status=status.HTTP_200_OK)

    def list(self, request):
        """Access a list of some/all Hurts"""

        hurts = Hurt.objects.all()

        # e.g. /hurts?patient_id=1
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            hurts = hurts.filter(patient_id=patient_id)

        show_inactive = self.request.query_params.get('show_inactive', None)
        if show_inactive is not None:
            if show_inactive == "false":
                hurts = hurts.filter(is_active=True)

        bodypart_id = self.request.query_params.get('bodypart_id', None)
        if bodypart_id is not None:
            hurts = hurts.filter(bodypart_id=bodypart_id)

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            # e.g. order_by=added_on-asc ; 'added_on' will be order, 'asc' will be direction
            order = order_by.split('-')[0]
            direction = order_by.split('-')[1]
            #if order is by 'recently updated', annotate the hurts with a value of their most recent update and order by that value 
            if order == 'recently_updated':
                hurts = hurts.annotate(
                    most_recent_update=Max('update__added_on'))
                order = 'most_recent_update'
            if direction == "desc":
                hurts = hurts.order_by(f"-{order}")
            if direction == "asc":
                hurts = hurts.order_by(f"{order}")

        for hurt in hurts:
            hurt.owner = False

            if hurt.patient == Patient.objects.get(user=request.auth.user):
                hurt.owner = True

        serializer = HurtSerializer(
            hurts, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """ Handle POST operations to /hurts

        Also creates an Update instance that is the first
        one for this Hurt

        Return:
            Response -- JSON Serialized Hurt instance
        """
        #
        patient = Patient.objects.get(user=request.auth.user)

        hurt = Hurt()
        hurt.patient = patient
        hurt.name = request.data["name"]
        hurt.is_active = request.data["is_active"]
        hurt.added_on = timezone.now()

        hurt.bodypart = Bodypart.objects.get(pk=request.data["bodypart_id"])

        try:
            hurt.save()
        except ValidationError as ex:
            return Response({"reason": ex.message})

        # extract treatment ids from request and try to convert that collection to a queryset of Treatment instances
        treatment_ids = request.data["treatment_ids"]

        try:
            treatments = [Treatment.objects.get(
                pk=treatment_id) for treatment_id in treatment_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # save bridge table relationships
        for treatment in treatments:
            hurt_treatment = HurtTreatment(
                hurt=hurt, treatment=treatment)
            hurt_treatment.save()

        # create an update for this Hurt
        update = Update()
        update.hurt = hurt
        update.added_on = timezone.now()
        update.pain_level = request.data["pain_level"]
        update.notes = request.data["notes"]
        update.save()

        serializer = HurtSerializer(hurt, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        """ Method to update a Hurt. Also calls and updates the assocaited first update 
            'added_on' and 'patient' values are not subject to update
        """
        try:
            hurt = Hurt.objects.get(pk=pk)
        except Hurt.DoesNotExist:
            return Response({'message': 'Hurt does not exist'}, status.HTTP_404_NOT_FOUND)

        # Save basic model values from request body
        hurt.name = request.data["name"]
        hurt.is_active = request.data["is_active"]

        # extract and save Bodypart by id from request body
        hurt.bodypart = Bodypart.objects.get(pk=request.data["bodypart_id"])

        # try to save the updated hurt
        try:
            hurt.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

        # extract treatment ids from request and try to convert that collection to a queryset of Treatment instances
        treatment_ids = request.data["treatment_ids"]

        try:
            treatments = [Treatment.objects.get(
                pk=treatment_id) for treatment_id in treatment_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # prune treatments that were previously associated if their id is no longer in the treatment_ids
        current_hurt_treatments = HurtTreatment.objects.filter(hurt=hurt)
        current_hurt_treatments.exclude(treatment__in=treatments).delete()

        # for the treatments that were still in (or are now added to) that array of ids, see if the relationship exists already; if not, create it
        for treatment in treatments:
            try:
                current_hurt_treatments.get(treatment=treatment)
            except HurtTreatment.DoesNotExist:
                new_hurt_treatment = HurtTreatment(
                    hurt=hurt, treatment=treatment)
                new_hurt_treatment.save()

        # find and update the first associated Update for this Hurt
        try:
            first_update = Update.objects.get(
                id=request.data["first_update_id"])
        except Update.DoesNotExist:
            return Response({'message': 'update does not exist, which is not so good'}, status=status.HTTP_404_NOT_FOUND)

        first_update.notes = request.data["notes"]
        first_update.pain_level = request.data["pain_level"]
        first_update.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):

        req_patient = Patient.objects.get(user=request.auth.user)

        try:
            hurt = Hurt.objects.get(pk=pk)
        except Hurt.DoesNotExist:
            return Response({'message': 'Hurt does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if not req_patient.id == hurt.patient.id:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        hurt.delete()

        return Response({}, status=status.HTTP_204_NO_CONTENT)
