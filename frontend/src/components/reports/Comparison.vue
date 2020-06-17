<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span>Validations comparison:</span>
            <v-spacer></v-spacer>
            <!-- Search field -->
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                hide-details
                class="pt-0 mt-0"
            ></v-text-field>

            <v-btn light small fab class="ml-4 elevation-5" @click="reportExcel">
                <v-icon>$excel</v-icon>
            </v-btn>
        </v-card-title>

        <!-- Validations list -->
        <v-col class="d-flex">
            <v-list dense flat class="ml-4">
                <v-list-item v-for="(item, i) in branches" :key="i">
                    <v-list-item-content class="py-0 my-1">
                        <v-list-item-title v-text="item"></v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>

            <v-spacer></v-spacer>

            <!-- Filtering type buttons -->
            <label class="d-flex align-start mt-4 mr-1 subtitle-1">
                Show:
                <v-btn-toggle
                    v-model="compareFiltering"
                    class="ml-2" color="teal" mandatory
                    @change="changeGrouping"
                >
                    <v-btn small v-for="name in compareFilters" :key="name">
                        {{ name }}
                    </v-btn>
                </v-btn-toggle>
            </label>

            <!-- Hide passed button -->
            <label class="d-flex align-start mt-4 mr-1 subtitle-1">
                <v-btn-toggle class="ml-2" color="teal">
                    <v-btn small @click="showHidePassed">
                        hide passed
                    </v-btn>
                </v-btn-toggle>
            </label>
        </v-col>

        <v-divider style="border-color: rgba(0, 0, 0, 0.3); height: 2px;"></v-divider>

        <!-- DataTable -->
        <v-data-table class="results-table"
            :headers="headers"
            :items="items"
            :search="search"
            :loading="reportLoading || excelLoading"
            disable-pagination hide-default-footer multi-sort
        >
            <template v-slot:item="{ item }">
                <tr>
                    <td v-for="(cellValue, index) in item" :key="index">
                        <v-chip v-if="STATUSES.includes(cellValue)" :color="getStatusColor(cellValue)" text-color="white" label>{{ cellValue }}</v-chip>
                        <span v-else>{{ cellValue }}</span>
                    </td>
                </tr>
            </template>
        </v-data-table>
    </v-card>
</template>

<script>
    import { mapState, mapGetters } from 'vuex'

    export default {
        data() {
            return {
                STATUSES: ['Passed', 'Failed', 'Skipped', 'Error', 'Blocked', 'Canceled'],
                search: '',

                compareFilters: ['all', 'diff'],
                compareFiltering: 0,
                showPassedPolicy: 0,
                showPassedPolicies: ['show_passed', 'hide_passed'],
            }
        },
        props: {
            type: { type: String, required: true }
        },
        computed: {
            ...mapState('tree', ['validations', 'branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading', 'headers', 'items']),
            url() {
                return `api/report/compare/${this.validations}`;
            }
        },
        methods: {
            reportExcel() {
                let urlParams = '?report=excel';
                this.$store
                    .dispatch('reports/reportExcel', {'url': this.url + urlParams})
                    .catch(error => {
                        this.$toasted.global.alert_error(error)
                    });
            },
            changeGrouping() {
                this.reportWeb();
            },
            showHidePassed(){
                this.showPassedPolicy = 1 - this.showPassedPolicy;
                this.reportWeb();
            },
            reportWeb() {
                let urlParams = `?show=${this.compareFilters[this.compareFiltering]},${this.showPassedPolicies[this.showPassedPolicy]}`;
                this.$store
                    .dispatch('reports/reportWeb', {'url': this.url + urlParams})
                    .catch(error => {
                        this.$toasted.global.alert_error(error)
                    });
            },
            /**
             * Coloring status column in comparison report
             */
            getStatusColor(s) {
                if (s == 'Passed') return 'green darken-1'
                else if (s == 'Failed') return 'red darken-4'
                else if (s == 'Error') return 'deep-orange darken-2'
                else if (s == 'Blocked') return 'grey darken-1'
                else if (s == 'Skipped') return 'cyan darken-3'
                else if (s == 'Canceled') return 'brown darken-3'
            },
        },
        mounted() {
            this.reportWeb();
        }
    }
</script>

<style>

</style>