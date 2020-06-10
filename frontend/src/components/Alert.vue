<template>
    <v-alert
        dismissible min-width="600"
        class="elevation-12"
        style="position: fixed; z-index: 100"
        transition="fade-transition"
        :type="alertObject.type"
        v-model="alert"
    >
        <span v-html="alertObject.message"></span>
    </v-alert>
</template>
<script>
import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';

export default {
    data() {
        return {}
    },
    props: {
    },
    computed: {
        ...mapState(['alertObject', 'isAlert', 'isAlertFading', 'isAlertReady']),
        alert: {
            get() {
                return !!this.isAlert;
            },
            set(v) {
                if (!v) { this.$store.commit("flushIsAlert") }
            }
        }
    },
    methods: {
    },
    watch: {
        isAlertReady() {
            if (this.alert && this.alertObject.fading) {
                setTimeout(() => {
                    this.alert = false;
                }, 1750)
            }
        }
    }
}
</script>