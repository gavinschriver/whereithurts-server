from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import TreatmentType

# Serializers
class TreatmentTypeSerializer(ModelSerializer):
    """ JSON serializer for the TreatmentType model  """
    class Meta:
        model = TreatmentType
        fields = ['id', 'name']
        depth = 1

    
# Viewset
class TreatmentTypeViewSet(ViewSet):
    """ ViewSet for the TreatmentType model """
    def list(self, request):
        try:
            treatment_types = TreatmentType.objects.all()
            serializer = TreatmentTypeSerializer(treatment_types, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
