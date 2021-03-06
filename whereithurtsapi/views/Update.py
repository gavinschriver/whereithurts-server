from rest_framework import response
from whereithurtsapi.models.Patient import Patient
from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Update, Hurt
from django.utils import timezone

# Serializers


class UpdateSerializer(ModelSerializer):
    class Meta:
        model = Update
        fields = ('id', 'added_on', 'notes', 'pain_level', 'hurt',
                  'is_first_update', 'date_added', 'pain_level_difference', 'owner')
        depth = 1

# Viewset


class UpdateViewSet(ViewSet):
    """ Access a single Update """

    def retrieve(self, request, pk=None):
        try:
            update = Update.objects.get(pk=pk)
        except Update.DoesNotExist:
            return Response({'message': 'Update does not exist'}, status=status.HTTP_404_NOT_FOUND)

        update.owner = False
        if update.hurt.patient == Patient.objects.get(user=request.auth.user):
            update.owner = True

        serializer = UpdateSerializer(update, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        updates = Update.objects.all()

        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            # prevent patients from accessing another patient's updates via q.string param
            requesting_patient = Patient.objects.get(user=request.auth.user)
            requested_patient = Patient.objects.get(pk=patient_id)
            if not requesting_patient == requested_patient:
                return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)
            updates = updates.filter(hurt__patient_id=patient_id)

        hurt_id = self.request.query_params.get('hurt_id', None)
        if hurt_id is not None:
            updates = updates.filter(hurt_id=hurt_id)

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            order = order_by.split('-')[0]
            direction = order_by.split('-')[1]

            if direction == "desc":
                updates = updates.order_by(f"-{order}")
            if direction == "asc":
                updates = updates.order_by(f"{order}")

        for update in updates:
            update.owner = False
            if update.hurt.patient == Patient.objects.get(user=request.auth.user):
                update.owner = True

        serializer = UpdateSerializer(
            updates, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """ create a single update """

        update = Update()

        update.hurt = Hurt.objects.get(pk=request.data["hurt_id"])

        if not update.hurt.patient.user == request.auth.user:
            return Response({'message': 'only owners of a Hurt can add an Update to it'}, status=status.HTTP_400_BAD_REQUEST)

        update.notes = request.data["notes"]
        update.pain_level = request.data["pain_level"]
        update.added_on = timezone.now()

        try:
            update.save()
        except ValidationError as ex:
            return Response({'message': ex.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = UpdateSerializer(update, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):

        req_patient = Patient.objects.get(user=request.auth.user)

        try:
            update = Update.objects.get(pk=pk)
        except Update.DoesNotExist:
            return Response({'message': 'Update does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if not req_patient.id == update.hurt.patient.id:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        update.hurt = Hurt.objects.get(pk=request.data["hurt_id"])
        update.notes = request.data["notes"]
        update.pain_level = request.data["pain_level"]

        update.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):

        req_patient = Patient.objects.get(user=request.auth.user)

        try:
            update = Update.objects.get(pk=pk)
        except Update.DoesNotExist:
            return Response({'message': 'Update does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if not req_patient.id == update.hurt.patient.id:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        update.delete()

        return Response({}, status=status.HTTP_204_NO_CONTENT)
