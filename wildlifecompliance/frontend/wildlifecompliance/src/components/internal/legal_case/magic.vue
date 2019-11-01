<template lang="html">
    <div id="CreateInspection">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="Shibaken" large force>
            <div>
                <img class="modal-content" src="../../../assets/img/shibaken.jpg" />
            </div>
        </modal>
    </div>
</template>
<script>
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';

export default {
    name: "Magic",
    data: function() {
      return {
        isModalOpen: false,
        //image: "/static/wildlifecompliance_vue/img/shibaken.jpg"
        //image: "/static/wildlifecompliance_vue/img/shibaken.c4c9d81.jpg"
        //image: "../../../assets/img/shibaken.jpg"
      }
    },
    components: {
      modal,
    },
    methods: {
    cancel: function() {
        this.isModalOpen = false;
    },
    ok: function() {
        this.isModalOpen = false;
    },
    close: function () {
        this.isModalOpen = false;
    },
    },
    created: async function() {
    }
};
</script>

<style lang="css">
</style>
