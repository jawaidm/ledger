<template id="returns_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Sanction Outcomes <small v-if="is_external">View any sanction outcome issued to you, pay any infringement notice and follow up on any remediation action</small>
                        <a :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pBody">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Type</label>
                                <select class="form-control" v-model="filterType">
                                    <option v-for="option in sanction_outcome_types" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Status</label>
                                <select class="form-control" v-model="filterStatus">
                                    <option v-for="option in sanction_outcome_statuses" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Payment status</label>
                                <select class="form-control" v-model="filterPaymentStatus">
                                    <option v-for="option in sanction_outcome_payment_statuses" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-3">
                            <label for="">Issue date from</label>
                            <div class="input-group date" ref="issueDateFromPicker">
                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateFrom">
                                <span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="">Issue date to</label>
                            <div class="input-group date" ref="issueDateToPicker">
                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateTo">
                                <span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="sanction_outcome_table" id="datatable_id" :dtOptions="table_options" :dtHeaders="table_headers"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'

export default {
    name: 'SanctionOutcomeTableDash',
    props: {
        level:{
            type: String,
            required: true,
            validator:function(val) {
                let options = ['internal','external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
        url:{
            type: String,
            required: true
        }
    },
    data() {
        let vm = this;
        return {
            sanction_outcome_types: [],
            sanction_outcome_statuses: [],
            sanction_outcome_payment_statuses: [],

            pBody: 'pBody' + vm._uid,
            datatable_id: 'return-datatable-'+vm._uid,

            filterType: 'all',
            filterStatus: 'all',
            filterPaymentStatus: 'all',
            filterDateFrom: '',
            filterDateTo: '',

            dateFormat: 'DD/MM/YYYY',
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            table_headers:["id", "Number", "Type", "Identifier", "Date", "Status", "Payment Status", "Sanction Outcome", "Action"],
            table_options:{
                serverSide: true,
                searchDelay: 1000,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                processing: true,
                ajax: {
                    url: vm.url,
                    dataSrc: 'data',
                    data: function (d) {
                        d.type = vm.filterType;
                        d.status = vm.filterStatus;
                        d.payment_status = vm.filterPaymentStatus;
                        d.date_from = vm.filterDateFrom;
                        d.date_to = vm.filterDateTo;
                    },
                    complete: function(jqXHR, textStatus){
                        // A function to be called when the request succeeds.
                        vm.$emit('records_total', jqXHR.responseJSON.recordsTotal);
                    }
                },
                columns: [
                    {
                        data: 'id',
                        visible: false,
                    },
                    {
                        data: 'lodgement_number',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'type',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data.name;
                        }
                    },
                    {
                        data: 'identifier',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'date_of_issue',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY') : '';
                        }
                    },
                    {
                        data: 'status',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data.name;
                        }
                    },
                    {
                        data: 'payment_status.name',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'paper_notices',
                        searchable: true,
                        orderable: false,
                        mRender: function (data, type, row){
                            let ret_str = ''

                            if (data.length > 0){
                                for (let i=0; i<data.length; i++){
                                    ret_str += '<a href="' + data[i][1] + '">' + data[i][0] + '</a><br />';
                                }
                            }

                            return ret_str;
                        }
                    },
                    {
                        mRender: function (data, type, full) {
                            if (full.status.id === 'awaiting_payment'){
                                //return '<a>Pay</a>';
                                return `<a href='#${full.id}' data-pay-infringement-penalty='${full.id}'>Pay</a><br/>`;
                            }
                            return '';
                        }
                    },
                ],
            }
        }
    },
    components:{
        datatable
    },
    watch:{
        filterType: function () {
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterStatus: function () {
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterPaymentStatus: function () {
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterDateFromPicker: function () {
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterDateToPicker: function () {
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
    },
    computed: {
        is_external: function(){
            return this.level == 'external';
        },
    },
    created: async function(){
        this.constructOptionsType();
        this.constructOptionsStatus();
        this.constructOptionsPaymentStatus();
    },
    methods:{
        addEventListeners: function () {
            this.attachFromDatePicker();
            this.attachToDatePicker();

            let vm = this;
            // External Pay Fee listener
            vm.$refs.sanction_outcome_table.vmDataTable.on('click', 'a[data-pay-infringement-penalty]', function(e) {
                e.preventDefault();
                var id = $(e.target).attr('data-pay-infringement-penalty');
                vm.payInfringementPenalty(id);
            });
        },
        payInfringementPenalty: function(sanction_outcome_id){
            console.log('payInfringementPenalty');
            //this.$http.post(helpers.add_endpoint_join(api_endpoints.sanction_outcome, sanction_outcome_id + '/sanction_outcome_infringement_penalty_checkout/'), sanction_outcome_id).then(res=>{
            this.$http.post('/infringement_penalty/' + sanction_outcome_id + '/').then(res=>{
                    window.location.href = "/ledger/checkout/checkout/payment-details/";
                },err=>{
                    swal(
                        'Submit Error',
                        helpers.apiVueResourceError(err),
                        'error'
                    )
                });
        },
        attachFromDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);

            el_fr.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_fr.on('dp.change', function (e) {
                if (el_fr.data('DateTimePicker').date()) {
                    vm.filterDateFromPicker = e.date.format('DD/MM/YYYY');
                    el_to.data('DateTimePicker').minDate(e.date);
                } else if (el_fr.data('date') === "") {
                    vm.filterDateFromPicker = "";
                }
            });
        },
        attachToDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);
            el_to.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_to.on('dp.change', function (e) {
                if (el_to.data('DateTimePicker').date()) {
                    vm.filterDateToPicker = e.date.format('DD/MM/YYYY');
                    el_fr.data('DateTimePicker').maxDate(e.date);
                } else if (el_to.data('date') === "") {
                    vm.filterDateToPicker = "";
                }
            });
        },
        constructOptionsType: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomeTypes', '/api/sanction_outcome/types.json');
            Object.assign(this.sanction_outcome_types, returned);
            this.sanction_outcome_types.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsStatus: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomeStatuses', '/api/sanction_outcome/statuses_for_external.json');
            Object.assign(this.sanction_outcome_statuses, returned);
            this.sanction_outcome_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsPaymentStatus: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomePaymentStatuses', '/api/sanction_outcome/payment_statuses.json');
            Object.assign(this.sanction_outcome_payment_statuses, returned);
            this.sanction_outcome_payment_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
      //  addEventListeners: function(){
      //      let vm = this;
      //      // Initialise Application Date Filters
      //       $(vm.$refs.dueDateToPicker).datetimepicker(vm.datepickerOptions);
      //       $(vm.$refs.dueDateToPicker).on('dp.change', function(e){
      //           if ($(vm.$refs.dueDateToPicker).data('DateTimePicker').date()) {
      //               vm.filterDueDateTo =  e.date.format('DD/MM/YYYY');
      //           }
      //           else if ($(vm.$refs.dueDateToPicker).data('date') === "") {
      //               vm.filterDueDateTo = "";
      //           }
      //        });
      //       $(vm.$refs.dueDateFromPicker).datetimepicker(vm.datepickerOptions);
      //       $(vm.$refs.dueDateFromPicker).on('dp.change',function (e) {
      //           if ($(vm.$refs.dueDateFromPicker).data('DateTimePicker').date()) {
      //               vm.filterDueDateFrom = e.date.format('DD/MM/YYYY');
      //               $(vm.$refs.dueDateToPicker).data("DateTimePicker").minDate(e.date);
      //           }
      //           else if ($(vm.$refs.dueDateFromPicker).data('date') === "") {
      //               vm.filterDueDateFrom = "";
      //           }
      //       });
      //       // End of Due Date Filters
      //  },
      //  initialiseSearch:function(){
      //      this.dateSearch();
      //  },
      //  dateSearch:function(){
      //      let vm = this;
      //      vm.$refs.return_datatable.table.dataTableExt.afnFiltering.push(
      //           function(settings,data,dataIndex,original){
      //               let from = vm.filterDateFrom;
      //               let to = vm.filterDateTo;
      //               let val = original.due_date;

      //               if ( from == '' && to == ''){
      //                   return true;
      //               }
      //               else if (from != '' && to != ''){
      //                   return val != null && val != '' ? moment().range(moment(from,vm.dateFormat),moment(to,vm.dateFormat)).contains(moment(val)) :false;
      //               }
      //               else if(from == '' && to != ''){
      //                   if (val != null && val != ''){
      //                       return moment(to,vm.dateFormat).diff(moment(val)) >= 0 ? true : false;
      //                   }
      //                   else{
      //                       return false;
      //                   }
      //               }
      //               else if (to == '' && from != ''){
      //                   if (val != null && val != ''){
      //                      return moment(val).diff(moment(from,vm.dateFormat)) >= 0 ? true : false;
      //                   }
      //                   else{
      //                       return false;
      //                   }
      //               }
      //               else{
      //                   return false;
      //               }
      //           }
      //      );
      //  }
    },
    mounted: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.addEventListeners();
            //vm.initialiseSearch();
        });
    }
}
</script>
<style scoped>
</style>
