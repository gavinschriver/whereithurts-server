from django.core.exceptions import ValidationError
from django.views.generic.base import View
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Hurt, Patient, Update, HurtTreatment, Treatment, Bodypart
from django.utils import timezone

#Serializers
class HurtSerializer(ModelSerializer):
    """JSON serializer for the Hurt model"""
    class Meta:
        model = Hurt
        fields = ('id','patient', 'bodypart', 'name', 'added_on', 'is_active', 'notes', 'pain_level')
        depth = 1

#Viewset 
class HurtViewSet(ViewSet):
    def list(self, request):
        """Access a list of some/all Hurts"""

        hurts = Hurt.objects.all()

        #e.g. /hurts?patient_id=1
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            hurts = hurts.filter(patient_id=patient_id)
        
        serializer = HurtSerializer(hurts, many=True, context={'request': request})
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
            return Response({"reason": ex.message })

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
        
        #create an update for this Hurt
        update = Update()
        update.hurt = hurt
        update.added_on = timezone.now()
        update.pain_level = request.data["pain_level"]
        update.notes = request.data["notes"]
        update.save()

        serializer = HurtSerializer(hurt, context={'request': request})
        return Response(serializer.data)





