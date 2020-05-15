<template>
    <v-alert
        :value="!!alert['message']"
        :type="alert['type']"
        dismissible min-width="600"
        class="elevation-12" style="position: fixed; z-index: 100" color="red darken-2"
        @input="closeAlert"
    >
        <span v-html="alert['message']"></span>
    </v-alert>
</template>
<script>
import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';

export default {
    data() {
        return {}
    },
    computed: {
        ...mapState(['alert']),
    },
    methods: {
        ...mapMutations(["setAlert"]),
        closeAlert(val) {
            this.setAlert({});
        },
    }
}
</script>