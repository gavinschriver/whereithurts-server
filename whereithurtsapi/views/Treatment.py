from whereithurtsapi.views.Hurt import HurtSerializer
from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Treatment, TreatmentType, Bodypart, TreatmentLink, Patient, Hurt, HurtTreatment
from django.utils import timezone

# Serializers 

class TreatmentLinkSerializer(ModelSerializer):
    """JSON Serializer for TreatmentLink model"""
    class Meta:
        model = TreatmentLink
        fields = ('id', 'linktext', 'linkurl')

class TreatmentSerializer(ModelSerializer):
    """JSON serializer for the Treatment model """
    hurts = HurtSerializer(many=True)
    links = TreatmentLinkSerializer(many=True)
    class Meta:
        model = Treatment
        fields = ('id','name', 'bodypart', 'treatmenttype', 'added_by', 'notes', 'public', 'links', 'hurts')
        depth = 1

#Viewset

class TreatmentViewSet(ViewSet):
    """ViewSet for the Treatment model """
    def create(self, request):
        """ Handle  POST operations to /treatments
        
        Return:
            Response --JSON Serialized Treatment instance
        """
        # find patient making this POST request and assign them as the patient for a new healing
        patient = Patient.objects.get(user=request.auth.user)

        treatment = Treatment()
        treatment.added_by = patient

        treatment.name = request.data["name"]
        treatment.notes = request.data["notes"]
        treatment.added_on = timezone.now()

        treatment.treatmenttype = TreatmentType.objects.get(pk=request.data["treatmenttype_id"])
        treatment.bodypart = Bodypart.objects.get(pk=request.data["bodypart_id"])

        # extract hurt ids from request and try to convert that collection to a queryset of Hurt instances
        hurt_ids = request.data["hurt_ids"]

        try:
            hurts = [Hurt.objects.get(pk=hurt_id) for hurt_id in hurt_ids]
        except Hurt.DoesNotExist:
            return Response({'message': 'request contains a hurt id for a non-existent hurt'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Try to save the new Treatment to the database
        try:
            treatment.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

        # save bridge table relationships)

        for hurt in hurts:
            hurt_treatment = HurtTreatment(hurt=hurt, treatment=treatment)
            hurt_treatment.save()

        #save links, maybe?
        treatment_links = request.data["treatment_links"]

        for treatment_link in treatment_links:
            new_treatment_link = TreatmentLink()
            new_treatment_link.linktext = treatment_link["linktext"]
            new_treatment_link.linkurl = treatment_link["linkurl"]
            new_treatment_link.treatment = treatment
            new_treatment_link.save()
        
        serializer = TreatmentSerializer(treatment, context={'request': request})
        return Response(serializer.data)


    def update(self, request, pk=None):
        """ Handle an update request for a treatment
        'user' and "added_on"  attributes are not subject to update

        'public' attribute is not currently implemented in client features
        """
        treatment = Treatment.objects.get(pk=pk)

        #save basic model values from request body
        treatment.name = request.data["name"]
        treatment.notes = request.data["notes"]

        #save related forgein-key items
        treatment.treatmenttype = TreatmentType.objects.get(pk=request.data["treatmenttype_id"])
        treatment.bodypart = Bodypart.objects.get(pk=request.data["bodypart_id"])

        # extract hurt ids from request and try to convert that collection to a queryset of Hurt instances
        hurt_ids = request.data["hurt_ids"]

        try:
            hurts = [Hurt.objects.get(pk=hurt_id) for hurt_id in hurt_ids]
        except Hurt.DoesNotExist:
            return Response({'message': 'request contains a hurt id for a non-existent hurt'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Try to save the updated Treatment to the database
        try:
            treatment.save()
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prune hurts that were previously associated if their id is no longer in the hurt_id array
        current_hurt_treatments = HurtTreatment.objects.filter(treatment=treatment) 
        current_hurt_treatments.exclude(hurt__in=hurts).delete()

        # for the hurts that were still in (or are now added to) that arrays of ids, see if the relationship exists already; if not, create it
        for hurt in hurts:
            try:
                current_hurt_treatments.get(hurt=hurt)
            except HurtTreatment.DoesNotExist:
                new_hurt_treatment = HurtTreatment(hurt=hurt, treatment=treatment)
                new_hurt_treatment.save()

        # delete pre-existing links, then save / re-save links according to request "treatment_link" list
        current_treatment_links = treatment.treatmentlink_set.all()
        current_treatment_links.delete()

        treatment_links = request.data["treatment_links"]

        for treatment_link in treatment_links:
            new_treatment_link = TreatmentLink()
            new_treatment_link.linktext = treatment_link["linktext"]
            new_treatment_link.linkurl = treatment_link["linkurl"]
            new_treatment_link.treatment = treatment
            new_treatment_link.save()
        
        serializer = TreatmentSerializer(treatment, context={'request': request})
        return Response(serializer.data)




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





