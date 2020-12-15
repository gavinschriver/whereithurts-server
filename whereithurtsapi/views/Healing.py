from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Healing, Patient, Treatment, HealingTreatment, HurtHealing, Hurt
from whereithurtsapi.views.Treatment import TreatmentSerializer
from whereithurtsapi.views.Hurt import HurtSerializer
from django.utils import timezone

# Serializers 

class HealingSerializer(ModelSerializer):
    """JSON serializer for the Healing model """
    treatments = TreatmentSerializer(many=True)
    hurts = HurtSerializer(many=True)
    class Meta:
        model = Healing
        fields = ('id', 'patient', 'notes', 'duration', 'added_on', 'treatments', 'hurts')
        depth = 1

#Viewset
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
            treatments = [Treatment.objects.get(pk=treatment_id) for treatment_id in treatment_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # extract hurt ids from request and try to convert that collection to a queryset of Hurt instances
        hurt_ids = request.data["hurt_ids"]

        try:
            hurts = [Hurt.objects.get(pk=hurt_id) for hurt_id in hurt_ids]
        except Treatment.DoesNotExist:
            return Response({'message': 'request contains a treatment id for a non-existent treatment'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        ## Try to save the new Healing to the database
        try:
            healing.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

        ## save bridge table relationships
        for treatment in treatments:
            healing_treatment = HealingTreatment(healing=healing, treatment=treatment)
            healing_treatment.save()
        
        for hurt in hurts:
            hurt_healing = HurtHealing(hurt=hurt, healing=healing)
            hurt_healing.save()

        ## serialize the new healing and send it back
        serialzier = HealingSerializer(healing, context={'request': request})
        return Response(serialzier.data)


    def list(self, request):
        """ Access a list of some/all Healings """
        healings = Healing.objects.all()

        #e.g. /healings?patient_id=1
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            healings = healings.filter(added_by_id=patient_id)

        serializer = HealingSerializer(healings, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """ Access a single Healing """
        try:
            healing = Healing.objects.get(pk=pk)
            serializer = HealingSerializer(healing, context={'request': request})
            return Response(serializer.data)
        except Healing.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
