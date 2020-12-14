from django.contrib.auth.models import User
import rest_framework
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Patient


# Serializers 
class PatientSerializer(ModelSerializer):
    """JSON serializer for the Patient model """
    class Meta:
        model = Patient
        fields = ('full_name', 'first_name', 'last_name', 'username', 'email')

#Viewset
class PatientViewSet(ViewSet):
    """ViewSet for the Patient model """
    def retrieve(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
            serializer = PatientSerializer(patient, context={'request': request})
            return Response(serializer.data)
        except Patient.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)


