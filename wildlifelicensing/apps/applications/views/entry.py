import tempfile

from datetime import datetime

from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files import File
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from ledger.accounts.models import EmailUser, Profile, Document
from ledger.accounts.forms import EmailUserForm, AddressForm, ProfileForm

from wildlifelicensing.apps.main.models import WildlifeLicenceType,\
    WildlifeLicenceCategory
from wildlifelicensing.apps.main.forms import IdentificationForm

from wildlifelicensing.apps.applications.models import Application, AmendmentRequest
from wildlifelicensing.apps.applications import utils
from wildlifelicensing.apps.applications.forms import ProfileSelectionForm
from wildlifelicensing.apps.applications.mixins import UserCanEditApplicationMixin
from wildlifelicensing.apps.main.mixins import OfficerRequiredMixin, OfficerOrCustomerRequiredMixin
from wildlifelicensing.apps.main.helpers import is_officer, is_customer

LICENCE_TYPE_NUM_CHARS = 2
LODGEMENT_NUMBER_NUM_CHARS = 6


class ApplicationEntryBaseView(TemplateView):
    login_url = '/'

    def get_context_data(self, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

        kwargs['licence_type'] = application.licence_type

        kwargs['customer'] = application.applicant

        kwargs['is_renewal'] = application.processing_status == 'renewal'

        return super(ApplicationEntryBaseView, self).get_context_data(**kwargs)


class NewApplicationView(OfficerOrCustomerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        utils.remove_temp_applications_for_user(request.user)

        application = Application.objects.create()

        utils.set_session_application(request.session, application)

        if is_customer(request.user):
            application.applicant = request.user
            application.save()

            return redirect('wl_applications:select_licence_type', *args, **kwargs)
        else:
            application.proxy_applicant = request.user
            application.save()
            return redirect('wl_applications:create_select_customer')


class EditApplicationView(UserCanEditApplicationMixin, View):
    def get(self, request, *args, **kwargs):
#         try:
#             utils.delete_app_session_data(request.session)
#         except Exception as e:
#             messages.warning(request, 'There was a problem deleting session data: %s' % e)
# 
#         temp_files_dir = tempfile.mkdtemp(dir=settings.MEDIA_ROOT)
#         utils.set_app_session_data(request.session, 'temp_files_dir', temp_files_dir)

#         application = get_object_or_404(Application, pk=args[1]) if len(args) > 1 else None
#         if application is not None:
#             utils.set_app_session_data(request.session, 'customer_pk', application.applicant_profile.user.pk)
#             utils.set_app_session_data(request.session, 'profile_pk', application.applicant_profile.pk)
#             utils.set_app_session_data(request.session, 'data', application.data)
# 
#             # copy document files into temp_files_dir
#             for document in application.documents.all():
#                 shutil.copyfile(document.file.path, os.path.join(temp_files_dir, document.name))
# 
#             if application.hard_copy is not None:
#                 shutil.copyfile(application.hard_copy.file.path, os.path.join(temp_files_dir, application.hard_copy.name))
#                 utils.set_app_session_data(request.session, 'application_document', application.hard_copy.name)
        try:
            utils.set_session_application(request.session, Application.objects.get(id=args[0]))
        except:
            messages.error(self.request, 'Unable to find application')
            return redirect('home')

        return redirect('wl_applications:enter_details')


class CreateSelectCustomer(OfficerRequiredMixin, TemplateView):
    template_name = 'wl/entry/create_select_customer.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        kwargs['create_customer_form'] = EmailUserForm(email_required=False)

        return super(CreateSelectCustomer, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        try:
            application = utils.get_session_application(request.session)
        except Exception as e:
            messages.error(request, e.message)
            return redirect('wl_applications:new_application')

        if 'select' in request.POST:
            application.applicant = EmailUser.objects.get(id=request.POST.get('customer'))
            application.save()
        elif 'create' in request.POST:
            create_customer_form = EmailUserForm(request.POST, email_required=False)
            if create_customer_form.is_valid():
                customer = create_customer_form.save()
                application.applicant = customer
                application.save()
            else:
                context = {'create_customer_form': create_customer_form}
                return render(request, self.template_name, context)

        return redirect('wl_applications:select_licence_type', *args, **kwargs)


class SelectLicenceTypeView(LoginRequiredMixin, TemplateView):
    template_name = 'wl/entry/select_licence_type.html'
    login_url = '/'

#     def get_context_data(self, **kwargs):
#         categories = {}
#
#         for category in WildlifeLicenceCategory.objects.all():
#             categories[category.name] = WildlifeLicenceType.objects.\
#                 filter(category=category, replaced_by__isnull=True).values('code_slug',
#                                                                            'name', 'code')
#
#         if WildlifeLicenceType.objects.filter(category__isnull=True, replaced_by__isnull=True).exists():
#             categories['Other'] = WildlifeLicenceType.objects.\
#                 filter(category__isnull=True, replaced_by__isnull=True).values('code_slug', 'name', 'code')
#
#         kwargs['licence_categories'] = categories
#
#         return super(SelectLicenceTypeView, self).get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        if args:
            try:
                application = utils.get_session_application(self.request.session)
            except Exception as e:
                messages.error(self.request, e.message)
                return redirect('wl_applications:new_application')

            application.licence_type = WildlifeLicenceType.objects.get(code_slug=self.args[0])
            application.save()

            return redirect('wl_applications:check_identification')

        categories = {}

        for category in WildlifeLicenceCategory.objects.all():
            categories[category.name] = WildlifeLicenceType.objects.\
                filter(category=category, replaced_by__isnull=True).values('code_slug',
                                                                           'name', 'code')

        if WildlifeLicenceType.objects.filter(category__isnull=True, replaced_by__isnull=True).exists():
            categories['Other'] = WildlifeLicenceType.objects.\
                filter(category__isnull=True, replaced_by__isnull=True).values('code_slug', 'name', 'code')

        return render(request, self.template_name, {'licence_categories': categories})


class CheckIdentificationRequiredView(LoginRequiredMixin, ApplicationEntryBaseView, FormView):
    template_name = 'wl/entry/upload_identification.html'
    form_class = IdentificationForm

    def get(self, *args, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#         licence_type = application.licence_type
# 
#         try:
#             applicant = utils.determine_applicant(self.request)
#         except utils.SessionDataMissingException as e:
#             messages.error(self.request, six.text_type(e))
#             return redirect('wl_applications:create_select_customer')

        if application.licence_type.identification_required and application.applicant.identification is None:
            return super(CheckIdentificationRequiredView, self).get(*args, **kwargs)
        else:
            return redirect('wl_applications:create_select_profile')

    def get_context_data(self, **kwargs):
        kwargs['file_types'] = ', '.join(['.' + file_ext for file_ext in IdentificationForm.VALID_FILE_TYPES])

        return super(CheckIdentificationRequiredView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#         try:
#             applicant = utils.determine_applicant(self.request)
#         except utils.SessionDataMissingException as e:
#             messages.error(self.request, six.text_type(e))
#             return redirect('wl_applications:create_select_customer')

        if application.applicant.identification is not None:
            application.applicant.identification.delete()

        application.applicant.identification = Document.objects.create(file=self.request.FILES['identification_file'])
        application.applicant.save()

        # update any other applications for this user that are awaiting ID upload
#       for application in Application.objects.filter(applicant_profile__user=applicant):
        for app in Application.objects.filter(applicant=application.applicant):
            if app.id_check_status == 'awaiting_update':
                app.id_check_status = 'updated'
                app.save()

        return redirect('wl_applications:create_select_profile', *self.args)


class CreateSelectProfileView(LoginRequiredMixin, ApplicationEntryBaseView):
    template_name = 'wl/entry/create_select_profile.html'

    def get_context_data(self, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#         if len(self.args) > 1:
#             kwargs['application_pk'] = self.args[1]

        kwargs['application_pk'] = application.id

#         try:
#             applicant = utils.determine_applicant(self.request)
#         except utils.SessionDataMissingException as e:
#             messages.error(self.request, six.text_type(e))
#             return redirect('wl_applications:create_select_customer')

        profile_exists = application.applicant.profile_set.count() > 0

        if application.applicant_profile is not None:
            kwargs['profile_selection_form'] = ProfileSelectionForm(user=application.applicant,
                                                                    selected_profile=application.applicant_profile)
        else:
            if profile_exists:
                kwargs['profile_selection_form'] = ProfileSelectionForm(user=application.applicant)

        if profile_exists:
            kwargs['profile_creation_form'] = ProfileForm(user=application.applicant)
        else:
            kwargs['profile_creation_form'] = ProfileForm(initial_display_name='Default',
                                                          initial_email=application.applicant.email,
                                                          user=application.applicant)

        kwargs['address_form'] = AddressForm()

        return super(CreateSelectProfileView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        try:
            application = utils.get_session_application(request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#        licence_type = WildlifeLicenceType.objects.get(code_slug=args[0])

        if 'select' in request.POST:
            profile_selection_form = ProfileSelectionForm(request.POST, user=application.applicant)

            if profile_selection_form.is_valid():
#               utils.set_app_session_data(request.session, 'profile_pk', profile_selection_form.cleaned_data.get('profile').id)
                application.applicant_profile = profile_selection_form.cleaned_data.get('profile')
                application.save()
            else:
                return render(request, self.template_name, {'licence_type': application.licence_type,
                                                            'profile_selection_form': profile_selection_form,
                                                            'profile_creation_form': ProfileForm(),
                                                            'address_form': AddressForm()})
        elif 'create' in request.POST:
            profile_form = ProfileForm(request.POST)
            address_form = AddressForm(request.POST)

            if profile_form.is_valid() and address_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.postal_address = address_form.save()
                profile.save()

#                utils.set_app_session_data(request.session, 'profile_pk', profile.id)
                application.applicant_profile = profile
                application.save()
            else:
                return render(request, self.template_name,
                              {'licence_type': application.licence_type,
                               'profile_selection_form': ProfileSelectionForm(user=request.user),
                               'profile_creation_form': profile_form, 'address_form': address_form})

        return redirect('wl_applications:enter_details')


class EnterDetailsView(UserCanEditApplicationMixin, ApplicationEntryBaseView):
    template_name = 'wl/entry/enter_details.html'

    def get_context_data(self, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#        application = get_object_or_404(Application, pk=self.args[1]) if len(self.args) > 1 else None

#        licence_type = WildlifeLicenceType.objects.get(code_slug=self.args[0])
#         if utils.is_app_session_data_set(self.request.session, 'profile_pk'):
#             profile = get_object_or_404(Profile, pk=utils.get_app_session_data(self.request.session, 'profile_pk'))
#         else:
#             profile = application.applicant_profile

#        kwargs['licence_type'] = application.licence_type
        kwargs['profile'] = application.applicant_profile
        kwargs['structure'] = application.licence_type.application_schema

        kwargs['is_proxy_applicant'] = is_officer(self.request.user)

#         if application is not None:
#             kwargs['application_pk'] = application.pk
        if application.review_status == 'awaiting_amendments':
            amendments = AmendmentRequest.objects.filter(application=application).filter(status='requested')
            kwargs['amendments'] = amendments

        if application.hard_copy is not None:
            kwargs['application_document'] = application.hard_copy.file.url

        if application.data:
            utils.convert_documents_to_url(application.data, application.documents.all(), '')

        kwargs['data'] = application.data

#         temp_files_dir = utils.get_app_session_data(self.request.session, 'temp_files_dir')
#         if temp_files_dir is not None:
#             temp_files_url = settings.MEDIA_URL + os.path.basename(os.path.normpath(temp_files_dir))
# 
#         if utils.is_app_session_data_set(self.request.session, 'data'):
#             data = utils.get_app_session_data(self.request.session, 'data')
# 
#             if temp_files_dir is not None:
#                 utils.prepend_url_to_files(application.licence_type.application_schema, data, temp_files_url)
# 
#             kwargs['data'] = data
# 
#         if utils.is_app_session_data_set(self.request.session, 'application_document'):
#             application_document = utils.get_app_session_data(self.request.session, 'application_document')
# 
#             if temp_files_dir is not None:
#                 application_document = os.path.join(temp_files_url, application_document)
# 
#             kwargs['application_document'] = application_document

        return super(EnterDetailsView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#         utils.rename_filename_doubleups(request.POST, request.FILES)

        application.data = utils.create_data_from_form(application.licence_type.application_schema,
                                                       request.POST, request.FILES)

#        utils.set_app_session_data(request.session, 'data', utils.create_data_from_form(licence_type.application_schema,
#                                                                                        request.POST, request.FILES))

#        temp_files_dir = utils.get_app_session_data(request.session, 'temp_files_dir')

        for f in request.FILES:
            if f == 'application_document':
                if application.hard_copy is None:
                    application.hard_copy = Document.objects.create(name='hard_copy')
                application.hard_copy.file = request.FILES[f]
                application.hard_copy.save()
            else:
                # for legacy applications, need to check if there's a document where file is
                # named by the file name rather than the form field name
                try:
                    document = application.documents.get(name=str(request.FILES[f]))
                except Document.DoesNotExist:
                    document, created = application.documents.get_or_create(name=f)

                document.name = f
                document.file = request.FILES[f]

                document.save()

        application.save()

        if 'draft' in request.POST or 'draft_continue' in request.POST:
#             if len(args) > 1:
#                 application = get_object_or_404(Application, pk=args[1])
#             else:
#                 application = Application()
# 
#             if is_officer(request.user):
#                 application.proxy_applicant = request.user

#             application.data = utils.get_app_session_data(request.session, 'data')
#             application.licence_type = WildlifeLicenceType.objects.get(code_slug=args[0])
#             application.applicant_profile = get_object_or_404(Profile,
#                                                               pk=utils.get_app_session_data(request.session, 'profile_pk'))
            application.customer_status = 'draft'

            if application.processing_status != 'renewal':
                application.processing_status = 'draft'

            application.save()
#             application.save(version_user=application.applicant_profile.user)
#
#             application.documents.clear()
#
#             # need to create documents from all the existing files that haven't been replaced
#             # (saved in temp_files_dir) as well as any new ones
#             try:
#                 for filename in utils.get_all_filenames_from_application_data(licence_type.application_schema,
#                                                                               utils.get_app_session_data(request.session, 'data')):
#
#                     # need to be sure file is in tmp directory (as it could be a freshly attached file)
#                     if os.path.exists(os.path.join(temp_files_dir, filename)):
#                         document = Document.objects.create(name=filename)
#                         with open(os.path.join(temp_files_dir, filename), 'rb') as doc_file:
#                             document.file.save(filename, File(doc_file), save=True)
#                             application.documents.add(document)
#             except Exception as e:
#                 messages.error(request, 'There was a problem appending applications files: %s' % e)
#
#             for f in request.FILES:
#                 if f == 'application_document':
#                     application.hard_copy = Document.objects.create(name=str(request.FILES[f]), file=request.FILES[f])
#                 else:
#                     application.documents.add(Document.objects.create(name=str(request.FILES[f]), file=request.FILES[f]))
# 
#             application.save(no_revision=True)

            messages.warning(request, 'The application was saved to draft.')

            if 'draft' in request.POST:
#                 try:
#                     utils.delete_app_session_data(request.session)
#                 except Exception as e:
#                     messages.warning(request, 'There was a problem deleting session data: %s' % e)

                return redirect('wl_dashboard:home')
#             else:
#                 # if continuing, need to save new files in temp so they can be previewed on enter details screen
#                 if len(request.FILES) > 0:
#                     temp_files_dir = utils.get_app_session_data(request.session, 'temp_files_dir')
# 
#                     for f in request.FILES:
#                         if f == 'application_document':
#                             utils.set_app_session_data(request.session, 'application_document', str(request.FILES[f]))
# 
#                         with open(os.path.join(temp_files_dir, str(request.FILES[f])), 'wb+') as destination:
#                             for chunk in request.FILES[f].chunks():
#                                 destination.write(chunk)
            else:
                return redirect('wl_applications:enter_details')
        else:
#             if len(request.FILES) > 0:
#                 temp_files_dir = utils.get_app_session_data(request.session, 'temp_files_dir')
# 
#                 for f in request.FILES:
#                     if f == 'application_document':
#                         utils.set_app_session_data(request.session, 'application_document', str(request.FILES[f]))
# 
#                     with open(os.path.join(temp_files_dir, str(request.FILES[f])), 'wb+') as destination:
#                         for chunk in request.FILES[f].chunks():
#                             destination.write(chunk)

            return redirect('wl_applications:preview')


class PreviewView(UserCanEditApplicationMixin, ApplicationEntryBaseView):
    template_name = 'wl/entry/preview.html'

    def get_context_data(self, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

        kwargs['profile'] = application.applicant_profile
        kwargs['structure'] = application.licence_type.application_schema

        kwargs['is_proxy_applicant'] = is_officer(self.request.user)

#         if len(self.args) > 1:
#             kwargs['application_pk'] = self.args[1]

#         temp_files_dir = utils.get_app_session_data(self.request.session, 'temp_files_dir')
#         if temp_files_dir is not None:
#             temp_files_url = settings.MEDIA_URL + os.path.basename(os.path.normpath(temp_files_dir))
# 
#         if utils.is_app_session_data_set(self.request.session, 'data'):
#             data = utils.get_app_session_data(self.request.session, 'data')
# 
#             if temp_files_dir is not None:
#                 utils.prepend_url_to_files(licence_type.application_schema, data, temp_files_url)
# 
#             kwargs['data'] = data
# 
#         if utils.is_app_session_data_set(self.request.session, 'application_document'):
#             application_document = utils.get_app_session_data(self.request.session, 'application_document')
# 
#             if temp_files_dir is not None:
#                 application_document = os.path.join(temp_files_url, application_document)
# 
        if application.data:
            utils.convert_documents_to_url(application.data, application.documents.all(), '')

        if application.hard_copy is not None:
            kwargs['structure'], kwargs['data'] = utils.append_app_document_to_schema_data(kwargs['structure'],
                                                                                           application.data,
                                                                                           application.hard_copy.file.url)
        else:
            kwargs['data'] = application.data

        return super(PreviewView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        try:
            application = utils.get_session_application(self.request.session)
        except Exception as e:
            messages.error(self.request, e.message)
            return redirect('wl_applications:new_application')

#         if is_officer(request.user):
#             application.proxy_applicant = request.user
# 
#         application.data = utils.get_app_session_data(self.request.session, 'data')
#         application.licence_type = get_object_or_404(WildlifeLicenceType, code_slug=args[0])
        application.correctness_disclaimer = request.POST.get('correctnessDisclaimer', '') == 'on'
        application.further_information_disclaimer = request.POST.get('furtherInfoDisclaimer', '') == 'on'
#         application.applicant_profile = get_object_or_404(Profile, pk=utils.get_app_session_data(request.session,
#                                                                                                  'profile_pk'))
        application.lodgement_sequence += 1
        application.lodgement_date = datetime.now().date()

        if application.customer_status == 'amendment_required':
            # this is a 're-lodged' application after some amendment were required.
            # from this point we assume that all the amendments have been amended.
            AmendmentRequest.objects.filter(application=application).filter(status='requested').update(status='amended')
            application.review_status = 'amended'
            application.processing_status = 'ready_for_action'
        else:
            if application.processing_status != 'renewal':
                application.processing_status = 'new'

        application.customer_status = 'under_review'

        # need to save application in order to get its pk
        if not application.lodgement_number:
#            application.save(no_revision=True)
            application.lodgement_number = '%s-%s' % (str(application.licence_type.pk).zfill(LICENCE_TYPE_NUM_CHARS),
                                                      str(application.pk).zfill(LODGEMENT_NUMBER_NUM_CHARS))

#         application.documents.clear()
# 
#         # if attached files were saved temporarily, add each to application as part of a Document
#         temp_files_dir = utils.get_app_session_data(request.session, 'temp_files_dir')
#         try:
#             for filename in utils.get_all_filenames_from_application_data(application.licence_type.application_schema,
#                                                                           utils.get_app_session_data(request.session, 'data')):
#                 document = Document.objects.create(name=filename)
#                 with open(os.path.join(temp_files_dir, filename), 'rb') as doc_file:
#                     document.file.save(filename, File(doc_file), save=True)
# 
#                     application.documents.add(document)
# 
#             if utils.is_app_session_data_set(request.session, 'application_document'):
#                 filename = utils.get_app_session_data(request.session, 'application_document')
#                 document = Document.objects.create(name=filename)
#                 with open(os.path.join(utils.get_app_session_data(request.session, 'temp_files_dir'), filename), 'rb') as doc_file:
#                     document.file.save(filename, File(doc_file), save=True)
# 
#                     application.hard_copy = document

        messages.success(request, 'The application was successfully lodged.')
#         except Exception as e:
#             messages.error(request, 'There was a problem creating the application: %s' % e)

        application.save(version_user=application.applicant_profile.user, version_comment='Details Modified')

#         try:
#             utils.delete_app_session_data(request.session)
#         except Exception as e:
#             messages.warning(request, 'There was a problem deleting session data: %s' % e)

        return redirect('wl_dashboard:home')


class RenewLicenceView(View):  # NOTE: need a UserCanRenewLicence type mixin
    def get(self, request, *args, **kwargs):
        try:
            utils.delete_app_session_data(request.session)
        except Exception as e:
            messages.warning(request, 'There was a problem deleting session data: %s' % e)

        previous_application = get_object_or_404(Application, licence=args[0])

        # check if there is already a renewal, otherwise create one
        try:
            application = Application.objects.get(previous_application=previous_application)
            if application.customer_status == 'under_review':
                messages.warning(request, 'A renewal for this licence has already been lodged and is awaiting review.')
                return redirect('wl_dashboard:home')
        except Application.DoesNotExist:
            application = utils.clone_application_for_renewal(previous_application)

        utils.set_app_session_data(request.session, 'customer_pk', application.applicant_profile.user.pk)
        utils.set_app_session_data(request.session, 'profile_pk', application.applicant_profile.pk)
        utils.set_app_session_data(request.session, 'data', application.data)
        utils.set_app_session_data(request.session, 'temp_files_dir', tempfile.mkdtemp(dir=settings.MEDIA_ROOT))

        return redirect('wl_applications:enter_details', application.licence_type.code_slug, application.pk, **kwargs)
