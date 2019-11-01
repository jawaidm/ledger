<template lang="html">
    <div class="container">
        <div class="row">
            <div class="col-md-3">
                <h3>Sanction Outcome: {{ displayLodgementNumber }}</h3>
            </div>
        </div>
        <div>
            <div class="col-md-3">
                <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
                <div class="row">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            Workflow 
                        </div>
                        <div class="panel-body panel-collapse">
                            <div class="row">
                                <div class="col-sm-12">
                                    <strong>Status</strong><br/>
                                    {{ statusDisplay }}<br/>
                                </div>
                            </div>

                            <div v-if="sanction_outcome.allocated_group" class="form-group">
                            <div class="row">
                                <div class="col-sm-12 top-buffer-s">
                                <strong>Currently assigned to</strong><br/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-12">
                                    <select :disabled="!sanction_outcome.user_in_group" class="form-control" v-model="sanction_outcome.assigned_to_id" @change="updateAssignedToId()">
                                        <option  v-for="option in sanction_outcome.allocated_group" :value="option.id" v-bind:key="option.id">
                                        {{ option.full_name }} 
                                        </option>
                                    </select>
                                </div>
                            </div>
                            </div>
                            <div v-if="sanction_outcome.user_in_group">
                                <a @click="updateAssignedToId('current_user')" class="btn pull-right">
                                    Assign to me
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            Action 
                        </div>
                        <div class="panel-body panel-collapse">

                            <div v-if="visibilityWithdrawButtonForInc" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('withdraw_by_inc')" class="btn btn-primary btn-block">
                                        Withdraw
                                    </a>
                                </div>
                            </div>

                            <div v-if="visibilityWithdrawButtonForManager" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('withdraw_by_manager')" class="btn btn-primary btn-block">
                                        Withdraw
                                    </a>
                                </div>
                            </div>

                            <div v-if="visibilitySendToManagerButton" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('send_to_manager')" class="btn btn-primary btn-block">
                                        Send to Manager
                                    </a>
                                </div>
                            </div>

                            <div v-if="visibilityEndorseButton" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('endorse')" class="btn btn-primary btn-block">
                                        Endorse
                                    </a>
                                </div>
                            </div>

                            <div v-if="visibilityDeclineButton" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('decline')" class="btn btn-primary btn-block">
                                        Decline
                                    </a>
                                </div>
                            </div>

                            <div v-if="visibilityReturnToOfficerButton" class="row action-button">
                                <div class="col-sm-12">
                                    <a @click="addWorkflow('return_to_officer')" class="btn btn-primary btn-block">
                                        Return to Officer
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-9" id="main-column">  
                <div class="row">
                    <div class="container-fluid">
                        <ul class="nav nav-pills aho2">
                            <li class="nav-item active"><a data-toggle="tab" :href="'#'+soTab">{{ typeDisplay }}</a></li>
                            <li class="nav-item"><a data-toggle="tab" :href="'#'+deTab">Details</a></li>
                            <li class="nav-item"><a data-toggle="tab" :href="'#'+reTab">Related Items</a></li>
                        </ul>
                        <div class="tab-content">
                            <div :id="soTab" class="tab-pane fade in active">
                                <FormSection :formCollapse="false" :label="typeDisplay">
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Identifier</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <input :readonly="readonlyForm" class="form-control" v-model="sanction_outcome.identifier"/>
                                        </div>
                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Offence</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <input readonly="true" class="form-control" v-model="displayOffence"/>
                                        </div>
                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Offender</label>
                                        </div>
                                        <div class="col-sm-6">

                                            <div v-if="sanction_outcome && sanction_outcome.offence && sanction_outcome.offence.offenders">
                                                <select :disabled="readonlyForm" class="form-control" v-model="sanction_outcome.offender">
                                                    <option value=""></option>
                                                    <option v-for="offender in sanction_outcome.offence.offenders" v-bind:value="offender" v-bind:key="offender.id">
                                                        <span v-if="offender.person">
                                                            {{ offender.person.first_name + ' ' + offender.person.last_name + ', DOB:' + offender.person.dob }} 
                                                        </span>
                                                        <span v-else-if="offender.organisation">
                                                            {{ offender.organisation.name + ', ABN: ' + offender.organisation.abn }} 
                                                        </span>
                                                    </option>
                                                </select>
                                            </div>

                                        </div>
                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-5">
                                            <label>Alleged committed offence</label>
                                        </div>
                                            <!--
                                        <div class="col-sm-6" v-for="item in sanction_outcome.alleged_offences">
                                            <input :readonly="readonlyForm" class="form-control" v-model="item.act + ', ' + item.name + ', ' + item.offence_text"/>
                                        </div>
                                            -->
                                        <div class="col-sm-12 form-group"><div class="row">
                                            <div class="col-sm-12">
                                                <datatable ref="alleged_committed_offence_table" id="alleged-committed-offence-table" :dtOptions="dtOptionsAllegedOffence" :dtHeaders="dtHeadersAllegedOffence" />
                                            </div>
                                        </div></div>

                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Issued on paper?</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <input :disabled="readonlyForm" class="col-sm-1" id="issued_on_paper_yes" type="radio" v-model="sanction_outcome.issued_on_paper" :value="true" />
                                            <label class="col-sm-1 radio-button-label" for="issued_on_paper_yes">Yes</label>
                                            <input :disabled="readonlyForm" class="col-sm-1" id="issued_on_paper_no" type="radio" v-model="sanction_outcome.issued_on_paper" :value="false" />
                                            <label class="col-sm-1 radio-button-label" for="issued_on_paper_no">No</label>
                                        </div>
                                    </div></div>

                                       <div class="col-sm-12 form-group"><div class="row">
                                           <div class="col-sm-3">
                                               <label class="control-label pull-left">Paper ID</label>
                                           </div>
                                           <div class="col-sm-7">
                                               <input type="text" :readonly="readonlyForm" class="form-control" name="paper_id" placeholder="" v-model="sanction_outcome.paper_id" :disabled="!sanction_outcome.issued_on_paper" /> 
                                           </div>
                                       </div></div>

                                       <div class="col-sm-12 form-group"><div class="row">
                                           <div class="col-sm-3">
                                               <label class="control-label pull-left">Paper notice</label>
                                           </div>
                                           <div id="paper_id_notice">
                                               <div v-if="sanction_outcome.issued_on_paper" class="col-sm-7">
                                                   <filefield ref="sanction_outcome_file" 
                                                              name="sanction-outcome-file" 
                                                              :documentActionUrl="sanction_outcome.sanctionOutcomeDocumentUrl" 
                                                              @update-parent="sanctionOutcomeDocumentUploaded" 
                                                              :isRepeatable="true" 
                                                              :readonly="readonlyForm" />
                                               </div>
                                           </div>
                                       </div></div>

                                </FormSection>
                            </div>

                            <div :id="deTab" class="tab-pane fade in">
                                <FormSection :formCollapse="false" label="Details">
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Description</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <textarea :disabled="readonlyForm" class="form-control" placeholder="add description" id="sanction-outcome-description" v-model="sanction_outcome.description"/>
                                        </div>
                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Date of Issue</label>
                                        </div>
                                        <!--
                                        <div class="col-sm-6">
                                            <input :readonly="readonlyForm" class="form-control" v-model="sanction_outcome.date_of_issue"/>
                                        </div>
                                        -->
                                        <div class="col-sm-3">
                                            <div class="input-group date" ref="dateOfIssuePicker">
                                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="sanction_outcome.date_of_issue" :disabled="!sanction_outcome.issued_on_paper || readonlyForm"/>
                                                <span class="input-group-addon">
                                                    <span class="glyphicon glyphicon-calendar"></span>
                                                </span>
                                            </div>
                                        </div>
                                    </div></div>

                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-3">
                                            <label>Time of Issue</label>
                                        </div>
<!--
                                        <div class="col-sm-6">
                                            <input :readonly="readonlyForm" class="form-control" v-model="sanction_outcome.time_of_issue"/>
                                        </div>
-->

                                        <div class="col-sm-3">
                                            <div class="input-group date" ref="timeOfIssuePicker">
                                                <input type="text" class="form-control" placeholder="HH:MM" v-model="sanction_outcome.time_of_issue" :disabled="!sanction_outcome.issued_on_paper || readonlyForm" />
                                                <span class="input-group-addon">
                                                    <span class="glyphicon glyphicon-calendar"></span>
                                                </span>
                                            </div>
                                        </div>
                                    </div></div>
                                </FormSection>
                            </div>

                            <div :id="reTab" class="tab-pane fade in">
                                <FormSection :formCollapse="false" label="Related Items" Index="4">
                                    <div class="col-sm-12 form-group"><div class="row">
                                        <div class="col-sm-12">
                                            <RelatedItems v-bind:key="relatedItemsBindId" :parent_update_related_items="setRelatedItems" :readonlyForm="readonlyForm" />
                                        </div>
                                    </div></div>
                                </FormSection>
                            </div>
                                
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="visibilitySaveButton" class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
            <div class="navbar-inner">
                <div class="container">
                    <p class="pull-right" style="margin-top:5px;">
                        <input type="button" @click.prevent="saveExit" class="btn btn-primary" value="Save and Exit"/>
                        <input type="button" @click.prevent="save" class="btn btn-primary" value="Save and Continue"/>
                    </p>
                </div>
            </div>
        </div>


        <div v-if="workflow_type">
            <SanctionOutcomeWorkflow ref="add_workflow" :workflow_type="workflow_type" v-bind:key="workflowBindId" />
        </div>
    </div>
</template>

<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import datatable from '@vue-utils/datatable.vue'
import utils from "@/components/external/utils";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import CommsLogs from "@common-components/comms_logs.vue";
import filefield from '@/components/common/compliance_file.vue';
import SanctionOutcomeWorkflow from './sanction_outcome_workflow';
import 'bootstrap/dist/css/bootstrap.css';
import hash from 'object-hash';
import RelatedItems from "@common-components/related_items.vue";

export default {
    name: 'ViewSanctionOutcome',
    data() {
        let vm = this;
        vm.STATUS_DRAFT = 'draft';
        vm.STATUS_AWAITING_ENDORSEMENT = 'awaiting_endorsement';
        vm.STATUS_AWAITING_REVIEW = 'awaiting_review';
        vm.STATUS_AWAITING_AMENDMENT = 'awaiting_amendment';
        vm.STATUS_AWAITING_PAYMENT = 'awaiting_payment';
        vm.STATUS_DECLINED = 'declined';

        return {
            temporary_document_collection_id: null,
            workflow_type :'',
            workflowBindId :'',
            soTab: 'soTab' + this._uid,
            deTab: 'deTab' + this._uid,
            reTab: 'reTab' + this._uid,
            objectHash : null,
            hashAttributeWhitelist: [
                'alleged_committed_offences',
                'allocated_group_id',
                'date_of_issue',
                'description',
                'district_id',
                'identifier',
                'issued_on_paper',
                'offence',
                'offender',
                'paper_id', 
                'paper_notices',
                'region_id',
                'time_of_issue',
                'type',
            ],
            comms_url: helpers.add_endpoint_json(
                api_endpoints.sanction_outcome,
                this.$route.params.sanction_outcome_id + "/comms_log"
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.sanction_outcome,
                this.$route.params.sanction_outcome_id + "/add_comms_log"
            ),
            logs_url: helpers.add_endpoint_json(
                api_endpoints.sanction_outcome,
                this.$route.params.sanction_outcome_id + "/action_log"
            ),
            dtHeadersAllegedOffence: [
                "id",
                "Act",
                "Section/Regulation",
                "Alleged Offence",
                "Action"
            ],
            dtOptionsAllegedOffence: {
                columns: [
                    {
                        data: "id",
                        visible: false
                    },
                    {
                        data: "Act",
                        mRender: function(data, type, row) {
                            let ret = data.alleged_offence.section_regulation.act;
                            if (!data.included){
                                ret = '<strike>' + ret + '</strike>';
                            }
                            return ret;
                        }
                    },
                    {
                        data: "Section/Regulation",
                        mRender: function(data, type, row) {
                            let ret = data.alleged_offence.section_regulation.name;
                            if (!data.included){
                                ret = '<strike>' + ret + '</strike>';
                            }
                            return ret;
                        }
                    },
                    {
                        data: "Alleged Offence",
                        mRender: function(data, type, row) {
                            let ret = data.alleged_offence.section_regulation.offence_text;
                            if (!data.included){
                                ret = '<strike>' + ret + '</strike>';
                            }
                            return ret;
                        }
                    },
                    {
                        data: "Action",
                        mRender: function(data, type, row) {
                            let ret = '';
                            if (!vm.readonlyForm && data.in_editable_status){
                                let checked_str = '';
                                let type_str = '';
                                let name_str = '';
                                let action_name = '';

                                if (vm.sanction_outcome.type.id == 'infringement_notice'){
                                    type_str = 'radio';
                                    name_str = ' name="aco_radio_group" ';
                                    if (data.included){
                                        checked_str = 'checked="checked"';
                                        action_name = '';
                                    } else {
                                        checked_str = '';
                                        action_name = 'Restore';
                                    }
                                } else {
                                    type_str = 'checkbox';
                                    name_str = ''
                                    if (data.included){
                                        checked_str = 'checked="checked"';
                                        action_name = 'Remove';
                                    } else {
                                        checked_str = '';
                                        action_name = 'Restore';
                                    }
                                }

                                ret = '<a><span class="include_alleged_committed_offence" data-alleged-committed-offence-id="' + data.id + '"/>' + action_name + '</span></a>';
                            }
                            return ret;
                        }
                    }
                ]
            }
        }
    },
    components: {
        FormSection,
        SanctionOutcomeWorkflow,
        CommsLogs,
        datatable,
        filefield,
        RelatedItems,
    },
    created: async function() {
        if (this.$route.params.sanction_outcome_id) {
            await this.loadSanctionOutcome({ sanction_outcome_id: this.$route.params.sanction_outcome_id });
            this.createStorageAllegedCommittedOffences();
            this.constructAllegedCommittedOffencesTable();
            this.updateObjectHash()
        }
    },
    mounted: function() {
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
    computed: {
        ...mapGetters('sanctionOutcomeStore', {
            sanction_outcome: "sanction_outcome",
        }),
        relatedItemsBindId: function() {
            let timeNow = Date.now()
            if (this.sanction_outcome && this.sanction_outcome.id) {
                return 'sanction_outcome_' + this.sanction_outcome.id + '_' + this._uid;
            } else {
                return timeNow.toString();
            }
        },
        readonlyForm: function() {
            return !this.canUserEditForm;
        },
        canUserEditForm: function() {
            let canUserEdit = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_AWAITING_AMENDMENT || this.sanction_outcome.status.id === this.STATUS_DRAFT){
                    canUserEdit = true;
                }
            }
            return canUserEdit;
        },
        statusDisplay: function() {
            let ret = '';
            if (this.sanction_outcome){
                if (this.sanction_outcome.status){
                    ret = this.sanction_outcome.status.name;
                }
            }
            return ret;
        },
        typeDisplay: function() {
            let ret = '';
            if (this.sanction_outcome){
                if (this.sanction_outcome.type){
                    ret = this.sanction_outcome.type.name;
                }
            }
            return ret;
        },
        displayOffence: function() {
            let ret = '';
            if (this.sanction_outcome){
                if (this.sanction_outcome.offence){
                    ret = this.sanction_outcome.offence.lodgement_number;
                }
            }
            return ret;
        },
        displayOffender: function() {
            let ret = '';
            if (this.sanction_outcome){
                if (this.sanction_outcome.offender){
                    if (this.sanction_outcome.offender.person){
                        ret = [this.sanction_outcome.offender.person.first_name, this.sanction_outcome.offender.person.last_name].filter(Boolean).join(" ");
                    } else if (this.sanction_outcome.offender.organisation){
                        ret = [this.sanction_outcome.offender.organisation.name, this.sanction_outcome.offender.organisation.abn].filter(Boolean).join(" ");
                    }
                }
            }
            return ret;
        },
        displayLodgementNumber: function() {
            let ret = '';
            if (this.sanction_outcome){
                ret = this.sanction_outcome.lodgement_number;
            }
            return ret;
        },
        visibilitySaveButton: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_DRAFT || this.sanction_outcome.status.id === this.STATUS_AWAITING_AMENDMENT){
                    visibility = true;
                }
            }
            return visibility;
        },
        visibilityWithdrawButtonForManager: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.type.id == 'infringement_notice'){
                    if (this.sanction_outcome.status.id === this.STATUS_AWAITING_ENDORSEMENT && this.sanction_outcome.issued_on_paper){
                        // Manager can withdraw paper issued infringement notice
                        visibility = true;
                    }
                }
            }
            return visibility;
        },
        visibilityWithdrawButtonForInc: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.type.id == 'infringement_notice'){
                    if (this.sanction_outcome.status.id === this.STATUS_AWAITING_PAYMENT){
                        // This is when Infringement Notice Coordinator withdraw
                        visibility = true;
                    }
                }
            }
            return visibility;
        },
        visibilitySendToManagerButton: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_DRAFT || this.sanction_outcome.status.id === this.STATUS_AWAITING_AMENDMENT){
                    visibility = true;
                }
            }
            return visibility;
        },
        visibilityEndorseButton: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_AWAITING_ENDORSEMENT || this.sanction_outcome.status.id === this.STATUS_AWAITING_REVIEW){
                    visibility = true;
                }
            }
            return visibility;
        },
        visibilityDeclineButton: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_AWAITING_ENDORSEMENT || this.sanction_outcome.status.id === this.STATUS_AWAITING_REVIEW){
                    if (!this.sanction_outcome.issued_on_paper){
                        // Only sanction outcome not issued on paper can be declined, otherwise withdraw
                        visibility = true;
                    }
                }
            }
            return visibility;
        },
        visibilityReturnToOfficerButton: function() {
            let visibility = false;
            if (this.sanction_outcome.can_user_action){
                if (this.sanction_outcome.status.id === this.STATUS_AWAITING_REVIEW){
                    visibility = true;
                }
            }
            return visibility;
        }
    },
    methods: {
        ...mapActions('sanctionOutcomeStore', {
            loadSanctionOutcome: 'loadSanctionOutcome',
            saveSanctionOutcome: 'saveSanctionOutcome',
            setAssignedToId: 'setAssignedToId',
            setCanUserAction: 'setCanUserAction',
            setRelatedItems: 'setRelatedItems',
        }),
        updateObjectHash: function() {
            this.objectHash = this.calculateHash();
        },
        calculateHash: function() {
            let copiedObject = {}
            Object.getOwnPropertyNames(this.sanction_outcome).forEach(
                (val, idx, array) => {
                    if (this.hashAttributeWhitelist.includes(val)) {
                        copiedObject[val] = this.sanction_outcome[val]
                    }
                });
            return hash(copiedObject);
        },
        formChanged: function(){
            let changed = false;
            if (!this.readonlyForm){
                if(this.objectHash !== this.calculateHash()){
                    changed = true;
                }
            }
            return changed;
        },
        sanctionOutcomeDocumentUploaded: function() {
            console.log('sanctionOutcomeDocumentUploaded');
        },
        createStorageAllegedCommittedOffences: function() {
            if (this.sanction_outcome && this.sanction_outcome.alleged_committed_offences){
                for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                    // We need to know if this alleged commited offence is already included in the sanction outcome 
                    // to manage Action column
                    this.sanction_outcome.alleged_committed_offences[i].already_included = this.sanction_outcome.alleged_committed_offences[i].included;
                }
            }
        },
        save: async function() {
            try {
                await this.saveSanctionOutcome();
                await swal("Saved", "The record has been saved", "success");

                this.constructAllegedCommittedOffencesTable();
                this.updateObjectHash()
            } catch (err) {
                this.processError(err);
            }
        },
        saveExit: async function() {
            try {
                await this.saveSanctionOutcome();
                await swal("Saved", "The record has been saved", "success");

                // remove redundant eventListeners
                window.removeEventListener('beforeunload', this.leaving);
                window.removeEventListener('onblur', this.leaving);

                this.$router.push({ name: 'internal-offence-dash' });
            } catch(err) {
                this.processError(err);
            }
        },
        processError: async function(err){
            let errorText = '';
            if (err.body.non_field_errors) {
                // When non field errors raised
                for (let i=0; i<err.body.non_field_errors.length; i++){
                    errorText += err.body.non_field_errors[i] + '<br />';
                }
            } else if(Array.isArray(err.body)) {
                // When general errors raised
                for (let i=0; i<err.body.length; i++){
                    errorText += err.body[i] + '<br />';
                }
            } else {
                // When field errors raised
                for (let field_name in err.body){
                    if (err.body.hasOwnProperty(field_name)){
                        errorText += field_name + ':<br />';
                        for (let j=0; j<err.body[field_name].length; j++){
                            errorText += err.body[field_name][j] + '<br />';
                        }
                    }
                }
            }
            await swal("Error", errorText, "error");
        },
        destroyed: function() {
            window.removeEventListener('beforeunload', this.leaving);
            window.removeEventListener('onblur', this.leaving);
        },
        setUpDateTimePicker: function() {
            let vm = this;
            let el_issue_date = $(vm.$refs.dateOfIssuePicker);
            let el_issue_time = $(vm.$refs.timeOfIssuePicker);

            // Issue "Date" field
            el_issue_date.datetimepicker({ format: "DD/MM/YYYY", maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_issue_date.on("dp.change", function(e) {
              if (el_issue_date.data("DateTimePicker").date()) {
                vm.sanction_outcome.date_of_issue = e.date.format("DD/MM/YYYY");
              } else if (el_issue_date.data("date") === "") {
                vm.sanction_outcome.date_of_issue = null;
              }
            });

            // Issue "Time" field
            el_issue_time.datetimepicker({ format: "LT", showClear: true });
            el_issue_time.on("dp.change", function(e) {
              if (el_issue_time.data("DateTimePicker").date()) {
                vm.sanction_outcome.time_of_issue = e.date.format("LT");
              } else if (el_issue_time.data("date") === "") {
                vm.sanction_outcome.time_of_issue = null;
              }
            });
        },
        addEventListeners: function() {
            this.setUpDateTimePicker();
            $("#alleged-committed-offence-table").on("click", ".remove_alleged_committed_offence", this.removeAllegedOffenceClicked);
            $("#alleged-committed-offence-table").on("click", ".restore_alleged_committed_offence", this.restoreAllegedOffenceClicked);
            $("#alleged-committed-offence-table").on("click", ".include_alleged_committed_offence", this.includeAllegedOffenceClicked);

            window.addEventListener('beforeunload', this.leaving);
            window.addEventListener('onblur', this.leaving);
        },
        leaving: function(e) {
            console.log('leaving');
            let vm = this;
            let dialogText = 'You have some unsaved changes.';
            if (vm.formChanged()){
                e.returnValue = dialogText;
                return dialogText;
            }
        },
        removeAllegedOffenceClicked: function(e) {
            let acoId = parseInt(e.target.getAttribute("data-alleged-committed-offence-id"));
            for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                if(acoId == this.sanction_outcome.alleged_committed_offences[i].id){
                    //this.sanction_outcome.alleged_committed_offences[i].removed = true;
                    this.sanction_outcome.alleged_committed_offences[i].included = false;
                }
            }
            this.constructAllegedCommittedOffencesTable();
        },
        includeAllegedOffenceClicked: function(e){
            let acoId = parseInt(e.target.getAttribute("data-alleged-committed-offence-id"));
            if(this.sanction_outcome.type.id == 'infringement_notice'){
                // Set false to all the alleged committed offences
                for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                    this.sanction_outcome.alleged_committed_offences[i].included = false;
                }
                // Set true to the alleged committed offence clicked
                for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                    if(acoId == this.sanction_outcome.alleged_committed_offences[i].id){
                        this.sanction_outcome.alleged_committed_offences[i].included = true
                    }
                }
            } else {
                for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                    if(acoId == this.sanction_outcome.alleged_committed_offences[i].id){
                        this.sanction_outcome.alleged_committed_offences[i].included = !this.sanction_outcome.alleged_committed_offences[i].included;
                    }
                }
            }
            this.constructAllegedCommittedOffencesTable();
        },
        restoreAllegedOffenceClicked: function(e){
            let acoId = parseInt(e.target.getAttribute("data-alleged-committed-offence-id"));
            for (let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                if(acoId == this.sanction_outcome.alleged_committed_offences[i].id){
                    //this.sanction_outcome.alleged_committed_offences[i].removed = false;
                    this.sanction_outcome.alleged_committed_offences[i].included = true;
                }
            }
            this.constructAllegedCommittedOffencesTable();
        },
        constructAllegedCommittedOffencesTable: function(){
            this.$refs.alleged_committed_offence_table.vmDataTable.clear().draw();
            if (this.sanction_outcome.alleged_committed_offences){
                for(let i=0; i<this.sanction_outcome.alleged_committed_offences.length; i++){
                    this.addAllegedOffenceToTable(this.sanction_outcome.alleged_committed_offences[i]);
                }
            }
        },
        addAllegedOffenceToTable: function(allegedCommittedOffence){
            this.$refs.alleged_committed_offence_table.vmDataTable.row.add({
                id: allegedCommittedOffence,
                Act: allegedCommittedOffence,
                "Section/Regulation": allegedCommittedOffence,
                "Alleged Offence": allegedCommittedOffence,
                Action: allegedCommittedOffence,
            }).draw();
        },
        addWorkflow(workflow_type) {
            this.workflow_type = workflow_type;
            this.updateWorkflowBindId();
            this.$nextTick(() => {
                this.$refs.add_workflow.isModalOpen = true;
            });
        },
        updateWorkflowBindId: function() {
            let timeNow = Date.now()
            if (this.workflow_type) {
                this.workflowBindId = this.workflow_type + '_' + timeNow.toString();
            } else {
                this.workflowBindId = timeNow.toString();
            }
        },
        updateAssignedToId: async function (user) {
            let url = helpers.add_endpoint_join(
                api_endpoints.sanction_outcome, 
                this.sanction_outcome.id + '/update_assigned_to_id/'
                );
            let payload = null;
            if (user === 'current_user' && this.sanction_outcome.user_in_group) {
                payload = {'current_user': true};
            } else if (user === 'blank') {
                payload = {'blank': true};
            } else {
                payload = { 'assigned_to_id': this.sanction_outcome.assigned_to_id };
            }
            let res = await Vue.http.post(
                url,
                payload
            );
            this.setAssignedToId(res.body.assigned_to_id);
            this.setCanUserAction(res.body.can_user_action);
            this.updateObjectHash();
        },
    }
}
</script>

<style>

</style>
