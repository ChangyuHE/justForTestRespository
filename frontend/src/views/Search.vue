<template>
    <v-container fluid>
    <v-row>
        <v-col cols=6 offset=3>
            <v-text-field
                v-debounce:3000ms="search"
                placeholder="What action do you want to perform?"
                :loading="queryLoading"
                :error-messages="errorMessage"
                :hint="recognizedQuery"
                persistent-hint
                clearable dense
                class="search-text-field"
            >
                <template v-slot:append-outer>
                    <v-tooltip bottom v-model="showTooltip">
                        <template v-slot:activator="{ on }">
                            <v-icon size="20" style="" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                        </template>
                        <div class="search-tooltip">
                            <p> Query string to perform actions. Examples of queries and their meanings: </p>
                            <p><b> dg1 18.04 </b> - compare 2 silicon dg1 ubuntu 18.04 </p>
                            <p><b> ats ubuntu emu </b> - compare 2 emulation ats ubuntu </p>
                            <p><b> best 3 ats sim rs2 </b> - best report of 3 silicon ats win 10 rs2 </p>
                            <p><b> last 4 ats sim win </b> - last report of 4 simulation ats windows </p>
                            <p><b> compare ats emu win with tgl lin </b> - compare 1 emulation ats windows with silicon tgl linux (ubuntu) </p>
                            <p><b> best 2 icl-lp 19h1 with tgl lin with sim adl win</b></p>
                            <p><b> last two slc dg1 win</b> - last 2 silicon windows 10 19h2 DG1</p>
                            <p> There are recognized query under query string, you can copy and paste it </p>
                        </div>
                    </v-tooltip>
                </template>
            </v-text-field>
        </v-col>
    </v-row>

    <v-row>
        <v-col cols=12 class='py-0'>
            <!-- Report card -->
            <component v-if="recognizedAction && !queryLoading" :is="reportName" :type="recognizedAction" />
        </v-col>
    </v-row>
    </v-container>
</template>

<script>
    import server from '@/server.js'
    import comparisonReport from '@/components/reports/Comparison.vue'
    import bestOrLastReport from '@/components/reports/BestOrLast.vue'
    import { mapState } from 'vuex'

    export default {
        components: {
            'compare-report': comparisonReport,
            'best-report': bestOrLastReport,
            'last-report': bestOrLastReport
        },
        data() {
            return {
                showTooltip: false,
                queryLoading: false,
                recognizedAction: '',
                recognizedQuery: '',
                errorMessage: '',
            }
        },
        computed: {
            ...mapState('tree', ['validations', 'branches']),
            ...mapState('reports', ['showReport', 'reportLoading']),
            reportName() {
                return `${this.recognizedAction}-report`
            }

        },
        methods: {
            search(query) {
                if (!query) return
                // The query is already being processed by the server
                if (this.queryLoading) return

                this.queryLoading = true;

                // load action to be performed, list of validations and their names
                let url = `api/report/search/?query=${query}`;
                server
                    .get(url)
                    .then(res => {
                        this.recognizedAction = res.data.action;
                        this.recognizedQuery = res.data.description;

                        // get valnames and validation ids from headers
                        let validationIds = res.data.validation_ids;
                        let valnames = res.data.valnames;
                        this.$store.dispatch('tree/setSelected', { validations: validationIds, branches: valnames });
                        this.errorMessage = '';
                    })
                    .catch(error => {
                        if (error.response){
                            if(error.response.status == 400 || error.response.status == 404) {
                                this.errorMessage = error.response.data;
                                this.$store.dispatch('tree/setSelected', { validations: [], branches: [] });
                                this.recognizedQuery = '';
                                this.recognizedAction = '';
                            } else {
                                console.log(error);
                                this.$toasted.global.alert_error_detailed({
                                    'header': `Error during searching`,
                                    'message': `${error}<br>URL: ${server.defaults.baseURL}/${url}<br>${error.response.data}`
                                })
                            }
                        } else {
                            console.log(error);
                        }
                    })
                    .finally(() => (this.queryLoading = false))
            },
        }
    }
</script>

<style scoped>
    .search-tooltip > p {
        margin-bottom: 0.5em !important;
    }
    .search-text-field >>> .v-messages__message {
        font-size: 17px;
        height: 18px;
        margin-top: 4px;
    }
    .v-tooltip__content > .search-tooltip {
        pointer-events: auto;
    }
</style>
