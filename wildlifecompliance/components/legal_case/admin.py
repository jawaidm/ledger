from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.legal_case import models
from reversion.admin import VersionAdmin


@admin.register(models.LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    pass

@admin.register(models.LegalCasePriority)
class LegalCasePriorityAdmin(admin.ModelAdmin):
    pass

