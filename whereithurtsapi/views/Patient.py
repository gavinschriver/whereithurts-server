from whereithurtsapi.models import Healing, Hurt, Treatment
from whereithurtsapi.views.Hurt import HurtSerializer, UpdateSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Patient


class TreatmentSerializer(ModelSerializer):
    """JSON serializer for Treatments attached to Patient retrieve """
    class Meta:
        model = Treatment
        fields = ('id', 'added_on', 'date_added',
                  'name', 'bodypart', 'treatmenttype')
        depth = 1


class HealingSerializer(ModelSerializer):
    """ JSON serializer for Healings attached to Patient retrieve """
    class Meta:
        model = Healing
        fields = ('id', 'added_on', 'date_added', 'notes')


class HurtSerializer(ModelSerializer):
    class Meta:
        model = Hurt
        fields = ('id', 'added_on', 'date_added',
                  'pain_level', 'notes', 'pain_level', 'name')


class PatientSerializer(ModelSerializer):
    """JSON serializer for the Patient model """
    class Meta:
        model = Patient
        fields = ('id', 'full_name', 'first_name',
                  'last_name', 'username', 'email')

# Viewset


class PatientViewSet(ViewSet):
    """ViewSet for the Patient model """

    def retrieve(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
            patient_data = PatientSerializer(
                patient, context={'request': request}).data

            updates = UpdateSerializer(patient.updates, many=True).data
            for update in updates:
                update.update({"activity_type": "Update"})

            healings = HealingSerializer(patient.healings, many=True).data
            for healing in healings:
                healing.update({"activity_type": "Healing"})

            hurts = HurtSerializer(patient.hurts, many=True).data
            for hurt in hurts:
                hurt.update({"activity_type": "Hurt"})

            treatments = TreatmentSerializer(
                patient.treatments, many=True).data
            for treatment in treatments:
                treatment.update({"activity_type": "Treatment"})

            recent_activity = updates + hurts + healings + treatments

            def by_date(row): return row["added_on"]

            recent_activity = sorted(
                recent_activity, key=by_date, reverse=True)[:5]

            patient_data["recent_activity"] = recent_activity
            return Response(patient_data)
        except Patient.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
