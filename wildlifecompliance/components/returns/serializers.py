from django.conf import settings
from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
    ReturnUserAction,
    ReturnLogEntry,
    ReturnSheet
)
from rest_framework import serializers


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'title',
            'organisation')


class ReturnSerializer(serializers.ModelSerializer):
    # activity = serializers.CharField(source='application.activity')
    processing_status = serializers.CharField(
        source='get_processing_status_display')
    submitter = EmailUserSerializer()
    sheet_activity_list = serializers.SerializerMethodField()
    sheet_species_list = serializers.SerializerMethodField()
    sheet_species = serializers.SerializerMethodField()
    table = serializers.SerializerMethodField()

    class Meta:
        model = Return
        fields = (
            'id',
            'application',
            'due_date',
            'processing_status',
            'submitter',
            'assigned_to',
            'lodgement_date',
            'nil_return',
            'licence',
            'resources',
            'table',
            'condition',
            'text',
            'type',
            'sheet_activity_list',
            'sheet_species_list',
            'sheet_species'
        )

    def get_sheet_activity_list(self, _return):
        """
        Gets the list of Activities available for a Return Running Sheet.
        :param _return: Return instance.
        :return: List of available activities.
        """
        return _return.sheet.get_activity_type_list() if _return.has_sheet else None

    def get_sheet_species_list(self, _return):
        """
        Gets the list of Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: List of species for a Return Running Sheet.
        """
        return _return.sheet.get_species_list() if _return.has_sheet else None

    def get_sheet_species(self, _return):
        """
        Gets the Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: species identifier for a Return Running Sheet.
        """
        return _return.sheet.species if _return.has_sheet else None

    def get_table(self, _return):
        """
        Gets the table of data available for the Return.
        :param _return: Return instance.
        :return: table of data details.
        """
        return _return.sheet.table if _return.has_sheet else _return.table


class ReturnTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnType
        fields = (
            'id',
            'resources'
        )


class ReturnActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = ReturnUserAction
        fields = '__all__'


class ReturnCommsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnLogEntry
        fields = '__all__'
