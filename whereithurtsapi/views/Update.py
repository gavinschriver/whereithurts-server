from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status   
from whereithurtsapi.models import Update

#Serializers 

class UpdateSerializer(ModelSerializer):
    class Meta:
        model = Update
        fields = ('id', 'added_on', 'notes', 'pain_level', 'hurt')
        depth = 1

#Viewset
class UpdateViewSet(ViewSet):
    """ Access a single Update """  
    def retrieve(self, request, pk=None):
        try:
            update = Update.objects.get(pk=pk)
        except Update.DoesNotExist:
            return Response({'message': 'Update does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UpdateSerializer(update, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    

