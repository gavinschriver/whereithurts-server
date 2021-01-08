from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Healing, Patient, Treatment, HealingTreatment, HurtHealing, Hurt
from whereithurtsapi.views.Treatment import TreatmentSerializer
from whereithurtsapi.views.Hurt import HurtSerializer
from whereithurtsapi.helpers import paginate
from django.utils import timezone
from django.db.models import Sum

# Serializers

class SimpleTreatmentSerializer(ModelSerializer):
    class Meta: 
        model = Treatment
        fields = ('id', 'name', 'notes')

class SimpleHealingSerializer(ModelSerializer):
    treatments = SimpleTreatmentSerializer(many=True)
    class Meta:
        model = Healing
        fields = ('id', 'date_added', 'added_on', 'duration', 'treatments')


class HealingSerializer(ModelSerializer):
    """JSON serializer for the Healing model """
    treatments = TreatmentSerializer(many=True)
    hurts = HurtSerializer(many=True)

    class Meta:
        model = Healing
        fields = ('id', 'patient', 'notes', 'duration',
                  'added_on', 'treatments', 'hurts', 'date_added', 'owner')
        depth = 1

# Viewset


class HealingViewSet(ViewSet):
    """ViewSet for the Healing model """

    def create(self, request):
        """ Handle POST operations to /healings

        Return:
            Response -- JSON Serialized Healing instance
        """
        # find patient making this POST request and assign them as the patient for a new healing
        patient = Patient.objects.get(user=request.auth.user)
        healing = Healing()
        healing.patient = patient

        # assign basic model values from request body
        healing.notes = request.data["notes"]
        healing.duration = request.data["duration"]
        healing.added_on = timezone.now()

        # extract treatment ids from request and try to convert that collection to a queryset of Treatment instances
        treatment_ids = request.data["treatment_ids"]

        try:
            treatments = [Treatment.objects.get(
                pk=treatment_id) for treatment_id in treatment_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # extract hurt ids from request and try to convert that collection to a queryset of Hurt instances
        hurt_ids = request.data["hurt_ids"]

        try:
            hurts = [Hurt.objects.get(pk=hurt_id) for hurt_id in hurt_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Try to save the new Healing to the database
        try:
            healing.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

        # save bridge table relationships
        for treatment in treatments:
            healing_treatment = HealingTreatment(
                healing=healing, treatment=treatment)
            healing_treatment.save()

        for hurt in hurts:
            hurt_healing = HurtHealing(hurt=hurt, healing=healing)
            hurt_healing.save()

        # serialize the new healing and send it back
        serialzier = HealingSerializer(healing, context={'request': request})
        return Response(serialzier.data)

    def update(self, request, pk=None):
        """ Handle an update request for a Healing
        'user', and 'added_on' attributes are not subject to update

        """
        healing = Healing.objects.get(pk=pk)

        # TO DO- insert validation for only authoring patient or admin to be allowed to edit

        # save basic model values from request body
        healing.notes = request.data["notes"]
        healing.duration = request.data["duration"]

        # extract treatment ids from request and try to convert that collection to a queryset of Treatment instances
        treatment_ids = request.data["treatment_ids"]

        try:
            treatments = [Treatment.objects.get(
                pk=treatment_id) for treatment_id in treatment_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # extract hurt ids from request and try to convert that collection to a queryset of Hurt instances
        hurt_ids = request.data["hurt_ids"]

        try:
            hurts = [Hurt.objects.get(pk=hurt_id) for hurt_id in hurt_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Try to save the updated Healing to the database
        try:
            healing.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

        # prune treatments and hurts that were previously associated with this healing if their id is no longer in the array of treatment_ids or hurt_ids
        current_healing_treatments = HealingTreatment.objects.filter(
            healing=healing)
        current_healing_treatments.exclude(treatment__in=treatments).delete()

        current_hurt_healings = HurtHealing.objects.filter(healing=healing)
        current_hurt_healings.exclude(hurt__in=hurts).delete()

        # for the treatments and hurts that were still in (or are now added to) those arrays of ids, see if the relationship exists already; if not, create it
        for treatment in treatments:
            try:
                current_healing_treatments.get(treatment=treatment)
            except HealingTreatment.DoesNotExist:
                new_healing_treatment = HealingTreatment(
                    healing=healing, treatment=treatment)
                new_healing_treatment.save()

        for hurt in hurts:
            try:
                current_hurt_healings.get(hurt=hurt)
            except HurtHealing.DoesNotExist:
                new_hurt_healing = HurtHealing(hurt=hurt, healing=healing)
                new_hurt_healing.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        """ Access a list of some/all Healings """

        # order by date descending (newest first) by default
        healings = Healing.objects.all().order_by('-added_on')

        order = self.request.query_params.get('order_by', None)
        direction = self.request.query_params.get('direction', None)
        hurt_id = self.request.query_params.get('hurt_id', None)
        patient_id = self.request.query_params.get('patient_id', None)
        page = request.query_params.get('page', None)
        page_size = request.query_params.get('page_size', 10)

        # e.g. /healings?hurt_id=1
        if hurt_id is not None:
            healings = healings.filter(hurt_healings__hurt_id=hurt_id)

        # e.g. /healings?order_by=added_on&direction=asc
        if order is not None:
            order_filter = order
            if direction is not None:
                if direction == "asc":
                    order_filter = f'{order}'
                elif direction == "desc":
                    order_filter = f'-{order}'

            healings = healings.order_by(order_filter)

        # e.g. /healings?patient_id=1
        if patient_id is not None:
            healings = healings.filter(patient_id=patient_id)


        #establish total time and count of current list after all filters are applied
        totalHealingTime = healings.aggregate(Sum('duration'))

        count = len(healings)

        if page is not None: 
            healings = paginate(healings, page, page_size)

        # serialize paginated healings     
        healinglist = SimpleHealingSerializer(
            healings, many=True, context={'request': request})

        # create response object
        healingData = {}
        healingData["healings"] = healinglist.data
        healingData["count"] = count
        healingData["total_healing_time"] = totalHealingTime["duration__sum"]
        return Response(healingData)

    def retrieve(self, request, pk=None):
        """ Access a single Healing """
        try:
            healing = Healing.objects.get(pk=pk)
            healing.owner = False 
            if healing.patient == Patient.objects.get(user=request.auth.user):
                healing.owner = True
            serializer = HealingSerializer(
                healing, context={'request': request})
            return Response(serializer.data)
        except Healing.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """ Delete a single Healing """
        try:
            healing = Healing.objects.get(pk=pk)
        except Healing.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        healing.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
