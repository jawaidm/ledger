from rest_framework import serializers

from wildlifecompliance.components.section_regulation.models import SectionRegulation


class SectionRegulationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SectionRegulation
        fields = (
            'id',
            'act',
            'name',
            'offence_text',
        )
        read_only_fields = ()