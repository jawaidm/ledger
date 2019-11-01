<template>
<div class="container" id="externalDash">
    <SanctionOutcomeDashTable level='external' :url='sanction_outcome_url'/>
</div>
</template>
<script>

import datatable from '@/utils/vue/datatable.vue'
import SanctionOutcomeDashTable from '@common-components/sanction_outcomes_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'ExternalDashboardSanctionOutcome',
    data() {
        let vm = this;
        return {
            sanction_outcome_url: helpers.add_endpoint_join(api_endpoints.sanction_outcome_paginated,'external_datatable_list/?format=datatables'),
            empty_list: '/api/empty_list',
        }
    },
    components:{
        SanctionOutcomeDashTable,
    },
    watch: {},
    computed: {
    },
    methods: {
    },
    mounted: function () {
    }
}
</script>
