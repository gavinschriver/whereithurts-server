from django.views.generic.base import View
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Hurt

#Serializers
class HurtSerializer(ModelSerializer):
    """JSON serializer for the Hurt model"""
    class Meta:
        model = Hurt
        fields = ('id','patient', 'bodypart', 'name', 'added_on', 'is_active')
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

