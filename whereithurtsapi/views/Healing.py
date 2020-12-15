from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Healing
from whereithurtsapi.views.Treatment import TreatmentSerializer

# Serializers 


class HealingSerializer(ModelSerializer):
    """JSON serializer for the Healing model """
    treatments = TreatmentSerializer(many=True)
    class Meta:
        model = Healing
        fields = ('id', 'patient', 'notes', 'duration', 'added_on', 'treatments')
        depth = 1

#Viewset
class HealingViewSet(ViewSet):
    """ViewSet for the Healing model """

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
