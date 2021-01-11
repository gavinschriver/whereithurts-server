from django.db.models.aggregates import Count
from whereithurtsapi.helpers.paginate import paginate
from whereithurtsapi.views.Hurt import HurtSerializer
from whereithurtsapi.views.Patient import PatientSerializer
from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, IntegerField
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from whereithurtsapi.models import Treatment, TreatmentType, Bodypart, TreatmentLink, Patient, Hurt, HurtTreatment
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import action


# Serializers


class TreatmentLinkSerializer(ModelSerializer):
    """JSON Serializer for TreatmentLink model"""
    class Meta:
        model = TreatmentLink
        fields = ('id', 'linktext', 'linkurl')


class TreatmentSerializer(ModelSerializer):
    """JSON serializer for the Treatment model """
    added_by = PatientSerializer(many=False)
    hurts = HurtSerializer(many=True)
    links = TreatmentLinkSerializer(many=True)

    class Meta:
        model = Treatment
        fields = ('id', 'name', 'bodypart', 'treatmenttype',
                  'added_by', 'notes', 'public', 'links', 'hurts', 'owner', 'healing_count', 'added_on')
        depth = 2


# Viewset


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
        treatment.public = request.data["public"]
        treatment.added_on = timezone.now()

        treatment.treatmenttype = TreatmentType.objects.get(
            pk=request.data["treatmenttype_id"])
        treatment.bodypart = Bodypart.objects.get(
            pk=request.data["bodypart_id"])

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

        # save links, maybe?
        treatment_links = request.data["treatment_links"]

        for treatment_link in treatment_links:
            new_treatment_link = TreatmentLink()
            new_treatment_link.linktext = treatment_link["linktext"]
            new_treatment_link.linkurl = treatment_link["linkurl"]
            new_treatment_link.treatment = treatment
            new_treatment_link.save()

        serializer = TreatmentSerializer(
            treatment, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        """ Handle an update request for a treatment
        'user' and "added_on"  attributes are not subject to update

        'public' attribute is not currently implemented in client features

        This method deletes all existing links from the DB for this treatment, then recreates them
        based on link object collection in the request body
        """
        treatment = Treatment.objects.get(pk=pk)

        # save basic model values from request body
        treatment.name = request.data["name"]
        treatment.notes = request.data["notes"]
        treatment.public = request.data["public"]

        # save related forgein-key items
        treatment.treatmenttype = TreatmentType.objects.get(
            pk=request.data["treatmenttype_id"])
        treatment.bodypart = Bodypart.objects.get(
            pk=request.data["bodypart_id"])

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
        current_hurt_treatments = HurtTreatment.objects.filter(
            treatment=treatment)
        current_hurt_treatments.exclude(hurt__in=hurts).delete()

        # for the hurts that were still in (or are now added to) that array of ids, see if the relationship exists already; if not, create it
        for hurt in hurts:
            try:
                current_hurt_treatments.get(hurt=hurt)
            except HurtTreatment.DoesNotExist:
                new_hurt_treatment = HurtTreatment(
                    hurt=hurt, treatment=treatment)
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

        serializer = TreatmentSerializer(
            treatment, context={'request': request})
        return Response(serializer.data)

    def list(self, request):
        """ Access a list of some/all Treatments """
        treatments = Treatment.objects.all().annotate(
            healings=Count('healing_treatments'))

        # e.g. /treatments?patient_id=1
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            treatments = treatments.filter(added_by_id=patient_id)

        # e.g. /treatments?bodypart_id=1
        bodypart_id = self.request.query_params.get('bodypart_id', None)
        if bodypart_id is not None:
            treatments = treatments.filter(bodypart_id=bodypart_id)

        # e.g. /treatments?treatmenttype_id=1
        treatmenttype_id = self.request.query_params.get(
            'treatmenttype_id', None)
        if treatmenttype_id is not None:
            treatments = treatments.filter(treatmenttype_id=treatmenttype_id)

        # e.g. /treatments?owner=1
        owner = self.request.query_params.get('owner', None)
        if owner is not None:
            treatments = treatments.filter(
                added_by_id=request.auth.user.patient.id)

        # e.g. /treatments?hurt_id=1
        hurt_id = self.request.query_params.get('hurt_id', None)
        if hurt_id is not None:
            treatments = treatments.filter(hurt_treatments__hurt_id=hurt_id)

        # e.g. /treatments?q=foot
        search_terms = self.request.query_params.get('q', None)
        if search_terms is not None:
            treatments = treatments.filter(Q(name__contains=search_terms) | Q(notes__contains=search_terms) | Q(
                bodypart__name__contains=search_terms) | Q(treatmenttype__name__contains=search_terms))

        order_by = self.request.query_params.get('order_by', None)
        direction = self.request.query_params.get('direction', None)
        if order_by is not None:
            order_filter = order_by
            if direction is not None:
                if direction == "desc":
                    order_filter = f'-{order_by}'
            
            treatments = treatments.order_by(order_filter)

        # e.g. make sure only results after any filtering are either belonging to current user OR public
        treatments = treatments.filter(
            Q(added_by_id=request.auth.user.patient.id) | Q(public=True))

        # e.g. /treatments?page=1
        page = request.query_params.get('page', None)
        page_size = request.query_params.get('page_size', 10)

        # add dynamic prop for client to use in determining whether a treatment's edit/delete controls should be visible
        for treatment in treatments:
            treatment.owner = False
            if treatment.added_by == Patient.objects.get(user=request.auth.user):
                treatment.owner = True

        # establish count of current list after all filtering
        count = len(treatments)

        if page is not None:
            treatments = paginate(treatments, page, page_size)

        # serialized paginated treatments

        treatmentList = TreatmentSerializer(
            treatments, many=True, context={'request': request})

        response = {}
        response["treatments"] = treatmentList.data
        response["count"] = count
        return Response(response)

    def retrieve(self, request, pk=None):
        """ Access a single Treatment """
        try:
            treatment = Treatment.objects.get(pk=pk)
            treatment.owner = False
            if treatment.added_by == Patient.objects.get(user=request.auth.user):
                treatment.owner = True
            serializer = TreatmentSerializer(
                treatment, context={'request': request})
            return Response(serializer.data)
        except Treatment.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """ Delete a single Treatment """
        try:
            treatment = Treatment.objects.get(pk=pk)
        except Treatment.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        treatment.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def tag_hurt(self, request, pk=None):
        try:
            treatment = Treatment.objects.get(pk=pk)
        except Treatment.DoesNotExist:
            return Response({'message': 'Treatment Does not Exist'}, status=status.HTTP_404_NOT_FOUND)

        try:
            hurt = Hurt.objects.get(pk=request.data["hurt_id"])
        except Hurt.DoesNotExist:
            return Response({'message': 'Hurt does not exist'}, status=status.HTTP_404_NOT_FOUND)

        #
        if request.method == "POST":
            try:
                hurt_treatment = HurtTreatment.objects.get(
                    hurt=hurt, treatment=treatment)
                return Response({'message': 'this treatment has already been tagged with this hurt'}, status=status.HTTP_400_BAD_REQUEST)
            except HurtTreatment.DoesNotExist:
                hurt_treatment = HurtTreatment()
                hurt_treatment.hurt = hurt
                hurt_treatment.treatment = treatment
                hurt_treatment.save()
                return Response({}, status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                hurt_treatment = HurtTreatment.objects.get(
                    hurt=hurt, treatment=treatment)
                hurt_treatment.delete()
                return Response({}, status=status.HTTP_204_NO_CONTENT)
            except HurtTreatment.DoesNotExist:
                return Response({'message': 'hurt has not been tagged on this treatment'}, status=status.HTTP_404_NOT_FOUND)

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
