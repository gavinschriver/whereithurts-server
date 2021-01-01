from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Bodypart

# Serializers
class BodypartSerializer(ModelSerializer):
    """ JSON serializer for the Bodypart model  """
    class Meta:
        model = Bodypart
        fields = ['id', 'name', 'hurt_image']
        depth = 1

    
# Viewset
class BodypartViewSet(ViewSet):
    """ ViewSet for the Bodypart model """
    def list(self, request):
        try:
            bodyparts = Bodypart.objects.all()
            serializer = BodypartSerializer(bodyparts, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
