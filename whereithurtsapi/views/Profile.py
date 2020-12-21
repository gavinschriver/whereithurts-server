from django.db.models.aggregates import Sum
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from whereithurtsapi.models import Patient, Healing, Treatment, Hurt
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

class ProfileHealingSerializer(ModelSerializer):
    class Meta: 
        model = Healing
        fields = ('id', 'duration', 'date_added', 'notes')

class ProfileTreatmentSerializer(ModelSerializer):
    class Meta:
        model = Treatment
        fields = ('id', 'name', 'notes', 'bodypart')
        depth = 1

class ProfileHurtSerializer(ModelSerializer):
    class Meta:
        model = Hurt
        fields = ('id', 'name', 'date_added', 'pain_level')


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

        #retrieve qset of this patient's healings for the past week
        recent_healings =  patient.healing_set.filter(added_on__gte=timezone.now() - timedelta(days=7))


        recent_healing_duration = recent_healings.aggregate(Sum('duration'))
        formatted_healing_time = timedelta(seconds=recent_healing_duration["duration__sum"])
        recent_treatments = Treatment.objects.filter(healing_treatments__healing__in=recent_healings)
        recent_hurts = Hurt.objects.filter(hurt_healings__healing__in=recent_healings)

        snapshot["recent_healings"] = ProfileHealingSerializer(recent_healings, many=True, context={'requet': request}).data
        snapshot["recent_treatments"] = ProfileTreatmentSerializer(recent_treatments, many=True, context={'request': request}).data
        snapshot["recent_hurts"] = ProfileHurtSerializer(recent_hurts, many=True, context={'request': request}).data
        snapshot["recent_healing_time"] = str(formatted_healing_time)


        return Response(snapshot)





        
        