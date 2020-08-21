<template>
    <comparison-report v-if="showReport" title='Validation overview:' type='Comparison'> </comparison-report>
</template>

<script>
    import server from '@/server'
    import comparisonReport from '@/components/reports/Comparison.vue'
    export default {
        components: {
            comparisonReport
        },

        data() {
            return {
                showReport: false,
            }
        },
        created() {
            let validationId = [this.$route.params.id]
            let valnames = []
            let url = `api/validations/flat/?ids=${validationId}`
            server
                .get(url)
                .then(response => {
                    valnames = response.data.map(validation => validation.name)
                    this.$store.dispatch('tree/setSelected', { validations: validationId, branches: valnames })
                    this.showReport = true
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Error during obtaining validation name', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
        }
    }
</script>

<style>

</style>