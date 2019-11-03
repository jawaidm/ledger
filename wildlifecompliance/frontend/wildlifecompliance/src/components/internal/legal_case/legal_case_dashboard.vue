<template>
    <div class="container" id="internalInspectionDash">
        <FormSection :label="`Case`" :Index="`0`">

        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterStatus">
                        <option v-for="option in statusChoices" :value="option.display" v-bind:key="option.id">
                            {{ option.display }}
                        </option>
                    </select>
                </div>
            </div>

        </div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Planned From</label>
                    <div class="input-group date" ref="caseCreatedDateFromPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterCaseCreatedFrom">
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Planned To</label>
                    <div class="input-group date" ref="caseCreatedDateToPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterCaseCreatedTo">
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
            </div>
            <div class="col-md-3 pull-right">
                <button @click.prevent="createLegalCase"
                    class="btn btn-primary pull-right">New Case</button>
            </div>    
        </div>
            

        <div class="row">
            <div class="col-lg-12">
                <datatable ref="legal_case_table" id="legal-case-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" />
            </div>
        </div>
        </FormSection>

        <!--FormSection :label="`Location`" :Index="`1`">
            <MapLocations />
        </FormSection-->

        <div v-if="legalCaseInitialised">
            <CreateLegalCaseModal ref="add_legal_case"  v-bind:key="createLegalCaseBindId"/>
        </div>

    </div>
</template>
<script>
    import $ from 'jquery'
    import datatable from '@vue-utils/datatable.vue'
    import Vue from 'vue'
    import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
    import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
    import FormSection from "@/components/forms/section_toggle.vue";
    import CreateLegalCaseModal from "./create_legal_case_modal.vue";
    
    export default {
        name: 'LegalCaseTableDash',
        data() {
            let vm = this;
            return {
                // classificationChoices: [],
                // Filters
                filterStatus: 'All',

                filterCaseCreatedFrom: '',
                filterCaseCreatedTo: '',
                // statusChoices: [],
                statusChoices: [],
                //inspectionTypes: [],
                
                dateFormat: 'DD/MM/YYYY',
                legalCaseInitialised: false,
                createLegalCaseBindId: '',
                // datepickerOptions: {
                //     format: 'DD/MM/YYYY',
                //     showClear: true,
                //     useCurrent: false,
                //     keepInvalid: true,
                //     allowInputToggle: true
                // },
                dtOptions: {
                    serverSide: true,
                    searchDelay: 1000,
                    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                    order: [
                        [0, 'desc']
                    ],
                    autoWidth: false,
                    rowCallback: function (row, data) {
                        $(row).addClass('appRecordRow');
                    },


                    language: {
                        processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                    },

                    responsive: true,
                    processing: true,
                    ajax: {
                        'url': '/api/legal_case_paginated/get_paginated_datatable/?format=datatables',
                        //'url': '/api/legal_case/datatable_list',
                        //'dataSrc': '',
                        //'dataSrc': 'data',
                        //'data': function(d) {
                        //    d.status_description = vm.filterStatus;
                        //    d.inspection_description = vm.filterInspectionType;
                        //    d.date_from = vm.filterPlannedFrom != '' && vm.filterPlannedFrom != null ? moment(vm.filterPlannedFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        //    d.date_to = vm.filterPlannedTo != '' && vm.filterPlannedTo != null ? moment(vm.filterPlannedTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        //}
                    },
                    //dom: 'lBfrtip',
                    //buttons: [
                    //    'excel',
                    //    'csv',
                    //    ],
                    columns: [
                        {
                            data: 'number',
                            searchable: false,
                            //orderable: false
                        },
                        {
                            data: 'title',
                            searchable: false,
                            orderable: true
                        },
                        {
                            data: 'status.name',
                            searchable: false,
                            orderable: true
                        },
                        {
                            data: 'created_date',
                            searchable: false,
                            orderable: true
                        },
                        {
                            data: "assigned_to",
                            searchable: false,
                            orderable: false,
                            mRender: function (data, type, full) {
                                if (data) {
                                    return data.full_name;
                                } else {
                                    return '';
                                }
                            }
                        },
                        {
                            data: 'user_action',
                            searchable: false,
                            orderable: false
                        },
                    ],
                },
                dtHeaders: [
                    'Number',
                    'Title',
                    'Status',
                    'Created Date',
                    'Assigned to',
                    'Action'
                ],
            }
        },

        beforeRouteEnter: function(to, from, next) {
            next(async (vm) => {
                // await vm.loadCurrentUser({ url: `/api/my_compliance_user_details` });
                // await this.datatablePermissionsToggle();
            });
        },
        
        created: async function() {
            // Status choices
            let returned_status_choices = await cache_helper.getSetCacheList(
                'LegalCase_StatusChoices', 
                '/api/legal_case/status_choices'
                );
            
            Object.assign(this.statusChoices, returned_status_choices);
            this.statusChoices.splice(0, 0, {id: 'all', display: 'All'});

        },
        watch: {
            filterStatus: function () {
                this.$refs.legal_case_table.vmDataTable.draw();
            },
            filterCaseCreatedFrom: function () {
                this.$refs.legal_case_table.vmDataTable.draw();
            },
            filterCaseCreatedTo: function () {
                this.$refs.legal_case_table.vmDataTable.draw();
            },
        },
        components: {
            datatable,
            FormSection,
            CreateLegalCaseModal,
        },
        computed: {
        },
        methods: {
            ...mapActions('legalCaseStore', {
                saveInspection: "saveLegalCase",
            }),
            createLegalCase: function() {
                this.setCreateLegalCaseBindId()
                this.legalCaseInitialised = true;
                this.$nextTick(() => {
                    this.$refs.add_legal_case.isModalOpen = true;
                });
            },
            setCreateLegalCaseBindId: function() {
                let timeNow = Date.now()
                this.createLegalCaseBindId = 'legal_case' + timeNow.toString();
            },
            createLegalCaseUrl: async function () {
                const newLegalCaseId = await this.saveLegalCase({ create: true });
                
                this.$router.push({
                    name: 'view-legal-case', 
                    params: { legal_case_id: newLegalCaseId}
                    });
            },
            addEventListeners: function () {
                let vm = this;
                // Initialise Planned Date Filters
                $(vm.$refs.caseCreatedDateToPicker).datetimepicker(vm.datepickerOptions);
                $(vm.$refs.caseCreatedDateToPicker).on('dp.change', function (e) {
                    if ($(vm.$refs.caseCreatedDateToPicker).data('DateTimePicker').date()) {
                        vm.filterCaseCreatedTo = e.date.format('DD/MM/YYYY');
                    } else if ($(vm.$refs.plannedDateToPicker).data('date') === "") {
                        vm.filterCaseCreatedTo = "";
                    }
                });
                $(vm.$refs.caseCreatedDateFromPicker).datetimepicker(vm.datepickerOptions);
                $(vm.$refs.caseCreatedDateFromPicker).on('dp.change', function (e) {
                    if ($(vm.$refs.caseCreatedDateFromPicker).data('DateTimePicker').date()) {
                        vm.filterCaseCreatedFrom = e.date.format('DD/MM/YYYY');
                    } else if ($(vm.$refs.caseCreatedDateFromPicker).data('date') === "") {
                        vm.filterCaseCreatedFrom = "";
                    }
                });
            },
            initialiseSearch: function () {
                this.dateSearch();
            },
            dateSearch: function () {
                let vm = this;
                vm.$refs.legal_case_table.table.dataTableExt.afnFiltering.push(
                    function (settings, data, dataIndex, original) {
                        let from = vm.filterCaseCreatedFrom;
                        let to = vm.filterCaseCreatedTo;
                        //let val = original.planned_for_date;
                        let val = original.case_created_date;

                        if (from == '' && to == '') {
                            return true;
                        } else if (from != '' && to != '') {
                            return val != null && val != '' ? moment().range(moment(from, vm.dateFormat),
                                moment(to, vm.dateFormat)).contains(moment(val)) : false;
                        } else if (from == '' && to != '') {
                            if (val != null && val != '') {
                                return moment(to, vm.dateFormat).diff(moment(val)) >= 0 ? true : false;
                            } else {
                                return false;
                            }
                        } else if (to == '' && from != '') {
                            if (val != null && val != '') {
                                return moment(val).diff(moment(from, vm.dateFormat)) >= 0 ? true : false;
                            } else {
                                return false;
                            }
                        } else {
                            return false;
                        }
                    }
                );
            },
        },
        mounted: async function () {
            let vm = this;
            $('a[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                }, 100);
            });
            this.$nextTick(async () => {
                await vm.initialiseSearch();
                await vm.addEventListeners();
            });
        }
    }
</script>
