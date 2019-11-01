<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row col-sm-12">

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left">Reason</label>
                        </div>
                        <div class="col-sm-7">
                            <textarea class="form-control" placeholder="add reason" id="reason" v-model="workflowDetails"/>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left"  for="Name">Attachments</label>
                        </div>
                        <div class="col-sm-9">
                            <filefield ref="comms_log_file" name="comms-log-file" :isRepeatable="true" :documentActionUrl="sanction_outcome.commsLogsDocumentUrl" />
                        </div>
                    </div></div>

                </div>

            </div>
            <div slot="footer">
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>
                                <span style="white-space: pre;" v-html="errorResponse"></span>
                            </strong>
                        </div>
                    </div>
                </div>
                <button type="button" v-if="processingDetails" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    name: "SanctionOutcomeWorkflow",
    data: function() {
        return {
            processingDetails: false,
            isModalOpen: false,
            files: [
                    {
                        'file': null,
                        'name': ''
                    }
            ],
            workflowDetails: '',
            errorResponse: '',

            allocatedGroup: [],
            allocated_group_id: null,
        }
    },
    components: {
      modal,
      filefield,
    },
    props:{
        workflow_type: {
            type: String,
            default: '',
        },
    },
    computed: {
        ...mapGetters('sanctionOutcomeStore', {
            sanction_outcome: "sanction_outcome",
        }),
        modalTitle: function() {
            switch(this.workflow_type){
                case 'withdraw_by_manager':
                    return "Withdraw";
                    break;
                case 'withdraw_by_inc':
                    return "Withdraw";
                    break;
                case 'send_to_manager':
                    return "Send to Manager";
                    break;
                case 'endorse':
                    return "Endorse";
                    break;
                case 'decline':
                    return "Decline";
                    break;
                case 'return_to_officer':
                    return "Return to Officer";
                    break;
                default:
                    return "---";
            }
        },
        regionDistrictId: function() {
            // if (this.district_id || this.region_id) {
            //     return this.district_id ? this.district_id : this.region_id;
            if (this.sanction_outcome.district || this.sanction_outcome.region) {
                return this.sanction_outcome.district ? this.sanction_outcome.district : this.sanction_outcome.region;
            } else {
                return null;
            }
      },
    //   groupPermission: function() {
    //       if (!this.workflow_type) {
    //           return "";  // TODO: make sure if this is correct
    //       } else if (this.workflow_type === 'send_to_manager') {
    //           return "manager";
    //       } else if (this.workflow_type === 'return_to_officer') {
    //           return "officer";
    //       } else if (this.workflow_type === 'endorse') {
    //           return "infringement_notice_coordinator";
    //       } else if (this.workflow_type === 'decline') {
    //           if (this.sanction_outcome.issued_on_paper) {
    //              return "officer";
    //           } else {
    //              return "manager";
    //           }
    //       } else if (this.workflow_type === 'withdraw') {
    //           return "infringement_notice_coordinator";
    //       } else if (this.workflow_type === 'close') {
    //           return "";  // TODO: make sure if this is correct
    //       }
    //   },
    },
    methods: {
        ...mapActions({
            loadAllocatedGroup: 'loadAllocatedGroup',  // defined in store/modules/user.js
        }),
        ok: async function () {
            try {
                this.processingDetails = true;
                const response = await this.sendData();
                this.close();
                this.$router.push({ name: 'internal-sanction-outcome-dash' });
            } catch (err){
                this.processError(err);
            } finally {
                this.processingDetails = false;
            }
        },
        processError: async function(err) {
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
            this.errorResponse = errorText;
        },
        cancel: async function() {
            await this.$refs.comms_log_file.cancel();
            this.isModalOpen = false;
            this.close();
        },
        close: function () {
            let vm = this;
            this.isModalOpen = false;
            let file_length = vm.files.length;
            this.files = [];
            for (var i = 0; i < file_length;i++){
                vm.$nextTick(() => {
                    $('.file-row-'+i).remove();
                });
            }
            this.attachAnother();
        },
        sendData: async function () {
            let post_url = '/api/sanction_outcome/' + this.sanction_outcome.id + '/workflow_action/'
            let payload = new FormData();
            payload.append('details', this.workflowDetails);
            this.$refs.comms_log_file.commsLogId ? payload.append('comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
            this.workflow_type ? payload.append('workflow_type', this.workflow_type) : null;

            let res = await Vue.http.post(post_url, payload);
            return res
        },
        uploadFile(target,file_obj){
            let vm = this;
            let _file = null;
            var file_input = $('.'+target)[0];
  
            if (file_input.files && file_input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(file_input.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = file_input.files[0];
            }
            file_obj.file = _file;
            file_obj.name = _file.name;
        },
        removeFile(index){
            let length = this.files.length;
            $('.file-row-'+index).remove();
            this.files.splice(index,1);
            this.$nextTick(() => {
                length == 1 ? this.attachAnother() : '';
            });
        },
        attachAnother(){
            this.files.push({
                'file': null,
                'name': ''
            })
        },
    },
}
</script>

<style>

</style>


