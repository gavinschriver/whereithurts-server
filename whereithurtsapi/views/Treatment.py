from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Treatment


# Serializers 
class TreatmentSerializer(ModelSerializer):
    """JSON serializer for the Treatment model """
    class Meta:
        model = Treatment
        fields = ('id','name', 'bodypart', 'treatmenttype', 'added_by', 'notes')
        depth = 1

#Viewset
class TreatmentViewSet(ViewSet):
    """ViewSet for the Treatment model """

    def list(self, request):
        """ Access a list of some/all Treatments """
        treatments = Treatment.objects.all()

        #e.g. /treatments?patient_id=1
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            treatments = treatments.filter(added_by_id=patient_id)

        serializer = TreatmentSerializer(treatments, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """ Access a single Treatment """
        try:
            treatment = Treatment.objects.get(pk=pk)
            serializer = TreatmentSerializer(treatment, context={'request': request})
            return Response(serializer.data)
        except Treatment.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)


