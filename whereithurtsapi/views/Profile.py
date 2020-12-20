from django.db.models.aggregates import Sum
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from whereithurtsapi.models import Patient, Healing, Treatment
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

class ProfileHealingSerializer(ModelSerializer):
    class Meta: 
        model = Healing
        fields = ('id', 'duration', 'date_added')

class ProfileTreatmentSerializer(ModelSerializer):
    class Meta:
        model = Treatment
        fields = ('id', 'name')


class ProfileViewSet(ViewSet):

    """ Method to access specific details of a Patient's use
    of the app based on timeframe. Patient id lookup is the PK
    of a /profiles route decorated by <patientId>/snapshot

    By default, will look up information for the past 7 days.
    """
    @action(detail=True)
    def snapshot(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'message': 'patient does not exist'}, status=status.HTTP_404_NOT_FOUND)

        snapshot = {}

        recent_healings =  patient.healing_set.filter(added_on__gte=timezone.now() - timedelta(days=7))

        recent_healing_time = recent_healings.aggregate(Sum('duration'))

        recent_treatments = Treatment.objects.filter(healing_treatments__healing__in=recent_healings)

        snapshot["recent_healings"] = ProfileHealingSerializer(recent_healings, many=True, context={'requet': request}).data
        snapshot["recent_treatments"] = ProfileTreatmentSerializer(recent_treatments, many=True, context={'request': request}).data
        snapshot["recent_healing_time"] = recent_healing_time["duration__sum"]


        return Response(snapshot)





        
        