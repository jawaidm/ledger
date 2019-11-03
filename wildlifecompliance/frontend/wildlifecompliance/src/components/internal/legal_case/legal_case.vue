<template lang="html">
    <div class="container">
      <div class="row">
        <div class="col-md-3">
          <h3>Case: {{ legal_case.number }}</h3>
        </div>
      </div>
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

                        <div v-if="legal_case.allocated_group" class="form-group">
                          <div class="row">
                            <div class="col-sm-12 top-buffer-s">
                              <strong>Currently assigned to</strong><br/>
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-sm-12">
                              <select :disabled="!legal_case.user_in_group" class="form-control" v-model="legal_case.assigned_to_id" @change="updateAssignedToId()">
                                <option  v-for="option in legal_case.allocated_group" :value="option.id" v-bind:key="option.id">
                                  {{ option.full_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div v-if="legal_case.user_in_group">
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
                        <div class="row action-button">
                            <div v-if="canUserAction" class="col-sm-12">
                                  <a @click="openInspection()" class="btn btn-primary btn-block" >
                                    Inspection
                                  </a>
                            </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="addWorkflow('endorse')" class="btn btn-primary btn-block">
                                  Witness Statement
                                </a>
                          </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="canUserAction && offenceVisibility" class="col-sm-12">
                                <a @click="openOffence()" class="btn btn-primary btn-block">
                                  Offence
                                </a>
                          </div>
                        </div>
                        
                        <div class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="addWorkflow('request_amendment')" class="btn btn-primary btn-block">
                                  Interview
                                </a>
                          </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <input 
                                :disabled="!sanctionOutcomeVisibility" 
                                type="button" 
                                class="btn btn-primary btn-block" 
                                value="Sanction Outcome" 
                                @click.prevent="openSanctionOutcome()" 
                                />
                                <!--a @click="openSanctionOutcome()" class="btn btn-primary btn-block">
                                  Sanction Outcome
                                </a-->
                          </div>
                        </div>
                        
                        <div  class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="open_sanction_outcome()" class="btn btn-primary btn-block">
                                  Brief of Evidence
                                </a>
                          </div>
                        </div>

                        <div id="close-button" class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="addWorkflow('close')" class="btn btn-primary btn-block">
                                  Close
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
                        <li class="nav-item active"><a data-toggle="tab" :href="'#'+runTab">Running Sheet</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+cTab" >Case Details</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+rTab">Related Items</a></li>
                    </ul>
                    <div class="tab-content">
                        <div :id="runTab" class="tab-pane fade in active">
                          <FormSection :formCollapse="false" label="Running Sheet" Index="0">
                            <div class="col-sm-12 form-group"><div class="row">
                                <div>
                                    <!--div class="col-sm-6"-->
                                        <label class="col-sm-10">Type !! to open Inspection or @@ to open Offence</label>
                                        <input id="test1" type="text" class="form-control" v-model="magicValue" />
                                        <!--label class="col-sm-4">Test 2</label>
                                        <input id="test2" type="text" class="form-control" /-->
                                    <!--/div-->

                                    <!--datatable ref="legal_case_table" id="legal-case-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" /-->
                                </div>
                            </div></div>
                          </FormSection>
                        </div>
                        <div :id="cTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Case Details">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Title
                                        <input :readonly="readonlyForm" type="text" class="form-control" v-model="legal_case.title" />
                                    </label>
                                </div></div>
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="legal_case.details" />
                                    </label>
                                </div></div>
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div v-if="legal_case.defaultDocumentUrl">
                                        <label class="col-sm-10">Documents
                                            <filefield 
                                            ref="legal_case_documents" 
                                            name="legal-case-documents" 
                                            :isRepeatable="true" 
                                            :documentActionUrl="legal_case.defaultDocumentUrl" 
                                            :readonly="readonlyForm"
                                            />
                                        </label>
                                    </div>
                                </div></div>
                            </FormSection>
                        </div>
                        <div :id="rTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Related Items">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div class="col-sm-12" v-if="relatedItemsVisibility">
                                        <RelatedItems v-bind:key="relatedItemsBindId" :parent_update_related_items="setRelatedItems" :readonlyForm="!canUserAction"/>
                                    </div>
                                </div></div>
                            </FormSection>
                        </div>
                    </div>
                </div>
            </div>
          </div>

        <div v-if="canUserAction" class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
            <div class="navbar-inner">
                <div class="container">
                    <p class="pull-right" style="margin-top:5px;">
                        <input type="button" @click.prevent="save('exit')" class="btn btn-primary" value="Save and Exit"/>
                        <input type="button" @click.prevent="save('noexit')" class="btn btn-primary" value="Save and Continue"/>
                    </p>
                </div>
            </div>
        </div>
        <!--div v-if="workflow_type">
          <InspectionWorkflow ref="add_workflow" :workflow_type="workflow_type" v-bind:key="workflowBindId" />
        </div-->
        <div v-if="offenceInitialised">
            <Offence 
            ref="offence" 
            :parent_update_function="loadLegalCase" 
            :region_id="legal_case.region_id" 
            :district_id="legal_case.district_id" 
            :allocated_group_id="legal_case.allocated_group_id" 
            v-bind:key="offenceBindId" 
            />
        </div>
        <div v-if="sanctionOutcomeInitialised">
            <SanctionOutcome 
            ref="sanction_outcome" 
            :parent_update_function="loadLegalCase"
            v-bind:key="sanctionOutcomeBindId" 
            />
        </div>
        <div v-if="inspectionInitialised">
            <Inspection
            ref="inspection" 
            :parent_update_function="loadLegalCase"
            v-bind:key="inspectionBindId" 
            />
        </div>
        <Magic ref="magic" />
        <!--InspectionWorkflow ref="inspection_workflow" :workflow_type="workflow_type" v-bind:key="workflowBindId" /-->
    </div>
</template>
<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import CommsLogs from "@common-components/comms_logs.vue";
import datatable from '@vue-utils/datatable.vue'
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import Offence from '../offence/offence_modal';
import SanctionOutcome from '../sanction_outcome/sanction_outcome_modal';
import Inspection from '../inspection/create_inspection_modal';
import filefield from '@/components/common/compliance_file.vue';
import RelatedItems from "@common-components/related_items.vue";
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import hash from 'object-hash';
import Magic from './magic';


export default {
  name: "ViewLegalCase",
  data: function() {
    return {
      uuid: 0,
      objectHash: null,
      runTab: 'runTab'+this._uid,
      rTab: 'rTab'+this._uid,
      cTab: 'cTab'+this._uid,
      current_schema: [],
      workflowBindId: '',
      workflow_type: '',
      comms_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/comms_log"
      ),
      comms_add_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/add_comms_log"
      ),
      logs_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/action_log"
      ),
      sanctionOutcomeInitialised: false,
      offenceInitialised: false,
      inspectionInitialised: false,
      hashAttributeWhitelist: [
        'allocated_group_id',
        'case_created_date',
        'case_created_time',
        'details',
        'title',
        'legal_case_priority_id',
        'region_id',
        'district_id',
      ],
      magicKeyPressed: false,
      magicKey2Pressed: false,
      magicValue: null,
      magic: true,
    };
  },
  components: {
    CommsLogs,
    FormSection,
    datatable,
    Offence,
    SanctionOutcome,
    filefield,
    RelatedItems,
    Inspection,
    Magic
  },
  computed: {
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    //...mapGetters({
    //    renderer_form_data: 'renderer_form_data'
    //}),
    csrf_token: function() {
      return helpers.getCookie("csrftoken");
    },
    statusDisplay: function() {
        return this.legal_case.status ? this.legal_case.status.name : '';
    },
    statusId: function() {
        return this.legal_case.status ? this.legal_case.status.id : '';
    },
    readonlyForm: function() {
        let readonly = true
        if (this.legal_case && this.legal_case.id) {
            readonly = !this.legal_case.can_user_action;
        }
        return readonly
        //return false
    },
    canUserAction: function() {
        let return_val = false
        if (this.legal_case && this.legal_case.id) {
            return_val = this.legal_case.can_user_action;
        }
        return return_val
    },
    offenceExists: function() {
        for (let item of this.legal_case.related_items) {
            if (item.model_name.toLowerCase() === 'offence') {
                return true
            }
        }
        // return false if no related item is an Offence
        return false
    },
    offenceVisibility: function() {
        let offence_visibility = false;
        if (this.legal_case.status && this.legal_case.can_user_action) {
            offence_visibility = this.legal_case.status.id === 'open' ? true : false;
        }
        return offence_visibility;
    },
    sanctionOutcomeVisibility: function() {
        let sanction_outcome_visibility = false;
        if (this.legal_case.status && this.offenceExists && this.legal_case.can_user_action) {
            sanction_outcome_visibility = this.legal_case.status.id === 'open' ? true : false;
        }
        return sanction_outcome_visibility;
    },
    relatedItemsBindId: function() {
        let timeNow = Date.now()
        let bindId = null;
        if (this.legal_case && this.legal_case.id) {
            bindId = 'legal_case_' + this.legal_case.id + '_' + this._uid;
        } else {
            bindId = timeNow.toString();
        }
        return bindId;
    },
    relatedItemsVisibility: function() {
        let related_items_visibility = false;
        if (this.legal_case && this.legal_case.id) {
            related_items_visibility = true;
        }
        return related_items_visibility;
    },
    offenceBindId: function() {
        let offence_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        offence_bind_id = 'offence' + parseInt(this.uuid);
        return offence_bind_id;
    },
    sanctionOutcomeBindId: function() {
        let sanction_outcome_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        sanction_outcome_bind_id = 'sanction_outcome' + parseInt(this.uuid);
        return sanction_outcome_bind_id;
    },
    inspectionBindId: function() {
        let inspection_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        inspection_bind_id = 'inspection' + parseInt(this.uuid);
        return inspection_bind_id;
    },
  },
  watch: {
      magicValue: {
          handler: function (){
              if (this.magicValue && 
                this.magicValue.toLowerCase().includes('shibaken') &&
                this.magic) {
                  //this.constructInspectionTeamTable();
                  this.magicMethod()
              }
          },
      },
  },
  filters: {
    formatDate: function(data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    }
  },
  methods: {
    ...mapActions('legalCaseStore', {
      loadLegalCase: 'loadLegalCase',
      saveLegalCase: 'saveLegalCase',
      setLegalCase: 'setLegalCase',
      setRelatedItems: 'setRelatedItems',
    }),
    openInspection() {
      this.uuid += 1;
      this.inspectionInitialised = true;
        this.$nextTick(() => {
          this.$refs.inspection.isModalOpen = true
      });
    },

    openSanctionOutcome(){
      this.uuid += 1;
      this.sanctionOutcomeInitialised = true;
      this.$nextTick(() => {
          this.$refs.sanction_outcome.isModalOpen = true;
      });
    },
    openOffence(){
      this.uuid += 1;
      this.offenceInitialised = true;
      this.$nextTick(() => {
          this.$refs.offence.isModalOpen = true;
      });
    },
    updateWorkflowBindId: function() {
        //let workflowBindId = ''
        let timeNow = Date.now()
        if (this.workflow_type) {
            this.workflowBindId = this.workflow_type + '_' + timeNow.toString();
        } else {
            this.workflowBindId = timeNow.toString();
        }
    },
    addWorkflow(workflow_type) {
      this.workflow_type = workflow_type;
      this.updateWorkflowBindId();
      this.$nextTick(() => {
        this.$refs.legal_case_workflow.isModalOpen = true;
      });
    },
    save: async function(returnToDash) {
      console.log(returnToDash)
      let savedLegalCase = null;
      //let savedPerson = null;
      if (this.legal_case.id) {
          savedLegalCase = await this.saveLegalCase({ create: false, internal: false });
      } else {
          savedLegalCase = await this.saveLegalCase({ create: true, internal: false });
      }
      this.calculateHash();
      //console.log(savedInspection);
      if (savedLegalCase && savedLegalCase.ok && returnToDash === 'exit') {
        // remove redundant eventListeners
        window.removeEventListener('beforeunload', this.leaving);
        window.removeEventListener('onblur', this.leaving);
        // return to dash
        this.$router.push({ name: 'internal-legal-case-dash' });
      }

    },
    magicMethod: function() {
        console.log("magic method");
        this.$refs.magic.isModalOpen = true;
        this.magic = false;
    },
    test1: function(e) {

        // keycode 49 = !
        if (e.which === 49 && this.magicKeyPressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            this.openInspection()
            this.magicKeyPressed = false;
        } else if (e.which === 49) {
            this.magicKeyPressed = true;
            // keycode 16 = Shift (must be pressed to access !)
        } else if (e.which === 50 && this.magicKey2Pressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            this.openOffence()
            this.magicKey2Pressed = false;
        } else if (e.which === 50) {
            this.magicKey2Pressed = true;
            // keycode 16 = Shift (must be pressed to access !)
        } else if (e.which === 16) {
            // pass
        } else if (this.magicValue && 
            this.magicValue.toLowerCase().includes('shibaken') &&
            this.magic) {
            //this.magic = true;
            this.magicMethod()
        } else {
            this.magicKeyPressed = false;
            this.magicKey2Pressed = false;
        }

    },
    addEventListeners: function() {
      let vm = this;
      let test1 = $('#test1');
      //let test2 = $('#test2');
      test1.on(
          'keydown', 
          function(e) {
              vm.test1(e)
          });

      //let el_fr_date = $(vm.$refs.plannedForDatePicker);
      //let el_fr_time = $(vm.$refs.plannedForTimePicker);
      //// "From" field
      //el_fr_date.datetimepicker({
      //  format: "DD/MM/YYYY",
      //  minDate: "now",
      //  showClear: true
      //});
      //el_fr_date.on("dp.change", function(e) {
      //  if (el_fr_date.data("DateTimePicker").date()) {
      //    vm.inspection.planned_for_date = e.date.format("DD/MM/YYYY");
      //  } else if (el_fr_date.data("date") === "") {
      //    vm.inspection.planned_for_date = "";
      //  }
      //});
      //el_fr_time.datetimepicker({ format: "LT", showClear: true });
      //el_fr_time.on("dp.change", function(e) {
      //  if (el_fr_time.data("DateTimePicker").date()) {
      //    vm.inspection.planned_for_time = e.date.format("LT");
      //  } else if (el_fr_time.data("date") === "") {
      //    vm.inspection.planned_for_time = "";
      //  }
      //});
      //$('#inspection-team-table').on(
      //    'click',
      //    '.remove_button',
      //    vm.removeTeamMember,
      //    );
      //$('#inspection-team-table').on(
      //    'click',
      //    '.make_team_lead',
      //    vm.makeTeamLead,
      //    );
      window.addEventListener('beforeunload', this.leaving);
      window.addEventListener('onblur', this.leaving);
    },
    leaving: function(e) {
        let vm = this;
        let dialogText = '';
        if (this.formChanged()){
            e.returnValue = dialogText;
            return dialogText;
        }
    },
    formChanged: function(){
        let changed = false;
        let copiedLegalCase = {};
        Object.getOwnPropertyNames(this.legal_case).forEach(
            (val, idx, array) => {
                if (this.hashAttributeWhitelist.includes(val)) {
                    copiedLegalCase[val] = this.legal_case[val]
                }
            });
        this.addHashAttributes(copiedLegalCase);
        if(this.objectHash !== hash(copiedLegalCase)){
            changed = true;
        }
        return changed;
    },
    calculateHash: function() {
        let copiedLegalCase = {}
        Object.getOwnPropertyNames(this.legal_case).forEach(
            (val, idx, array) => {
                if (this.hashAttributeWhitelist.includes(val)) {
                    copiedLegalCase[val] = this.legal_case[val]
                }
            });
        this.addHashAttributes(copiedLegalCase);
        this.objectHash = hash(copiedLegalCase);
    },
    addHashAttributes: function(obj) {
        let copiedRendererFormData = Object.assign({}, this.renderer_form_data);
        obj.renderer_form_data = copiedRendererFormData;
        return obj;
    },
    updateAssignedToId: async function (user) {
        let url = helpers.add_endpoint_join(
            api_endpoints.legal_case,
            this.legal_case.id + '/update_assigned_to_id/'
            );
        let payload = null;
        if (user === 'current_user' && this.legal_case.user_in_group) {
            payload = {'current_user': true};
        } else if (user === 'blank') {
            payload = {'blank': true};
        } else {
            payload = { 'assigned_to_id': this.legal_case.assigned_to_id };
        }
        let res = await Vue.http.post(
            url,
            payload
        );
        await this.setLegalCase(res.body);
    },
  },
  created: async function() {
      if (this.$route.params.legal_case_id) {
          await this.loadLegalCase({ legal_case_id: this.$route.params.legal_case_id });
      }
      console.log(this)

      this.calculateHash();
  },
  destroyed: function() {
      window.removeEventListener('beforeunload', this.leaving);
      window.removeEventListener('onblur', this.leaving);
  },

  mounted: function() {
      this.$nextTick(async () => {
          this.addEventListeners();
      });
  },
};
</script>

<style lang="css">
.action-button {
    margin-top: 5px;
}
#close-button {
  margin-bottom: 50px;
}
.awesomplete {
    width: 100% !important;
}
.nav>li>a:focus, .nav>li>a:hover {
  text-decoration: none;
  background-color: #eee;
}
.nav-item {
  background-color: hsla(0, 0%, 78%, .8) !important;
  margin-bottom: 2px;
}
</style>
