from rest_framework import serializers
from wildlifecompliance.components.main.models import CommunicationsLogEntry, TemporaryDocumentCollection
from ledger.accounts.models import EmailUser


class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=EmailUser.objects.all(), required=False)
    documents = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'log_type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'application'
            'documents'
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class SearchKeywordSerializer(serializers.Serializer):
    number = serializers.CharField()
    record_id = serializers.IntegerField()
    record_type = serializers.CharField()
    applicant = serializers.CharField()
    text = serializers.JSONField(required=False)
    licence_document = serializers.CharField(
        source='licence_document._file.url',
        required=False
    )


class SearchReferenceSerializer(serializers.Serializer):
    url_string = serializers.CharField()


#class TemporaryDocumentSerializer(serializers.Serializer):
#    temp_document_collection_id = serializers.IntegerField()
#    uploaded_file = serializers.FileField(max_length=255)

class TemporaryDocumentCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporaryDocumentCollection
        fields = ('id',)
