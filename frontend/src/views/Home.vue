<template>
    <v-row>
        <v-col class="pt-2">
            <splitpanes class="default-theme" ref="split" @pane-maximize="showExpand = true" @resize="showExpand = false">
                <!-- Left part -->
                <pane size="40" max-size="50">
                    <div class="d-flex">
                        <!-- ">" button to show double-clicked pane -->
                        <v-btn v-if="showExpand"
                            fab x-small absolute fixed class="mt-2"
                            color="blue-grey lighten-4"
                            @click="expandPane"
                        >
                            <v-icon>mdi-chevron-right</v-icon>
                        </v-btn>
                        <!-- Validations tree -->
                        <v-card width="100%" class="elevation-0 ml-1" color="transparent">
                            <validations-tree ref="validations-tree"/>
                        </v-card>
                    </div>
                </pane>
                <!-- Right part -->
                <pane>
                    <div class="ml-4 mr-1 mt-2" :style="{position: reportIsReadyToBeRendered ? 'relative': 'fixed'}">
                        <!-- Buttons toolbar -->
                        <v-toolbar tile class="elevation-3">
                            <v-btn-toggle
                                color="teal darken-1"
                                v-model="reportType" @change="reportClick"
                            >
                                <!-- Best report button -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length"
                                    :loading="reportTypeLoading('best')"
                                    value="best"
                                    title="Best results report"
                                >
                                    Best results
                                </v-btn>

                                <!-- Last report button -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length"
                                    :loading="reportTypeLoading('last')"
                                    value="last"
                                    title="Last results report"
                                >
                                    Last results
                                </v-btn>

                                <!-- Comparison report -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length"
                                    :loading="reportTypeLoading('compare')"
                                    value="comparison"
                                    :title="compareButtonName"
                                >
                                    {{ compareButtonName }}
                                </v-btn>

                                <!-- Indicator report -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length || (validations.length !== 1)"
                                    :loading="reportTypeLoading('indicator')"
                                    value="indicator"
                                    title="Indicator"
                                >
                                    Indicator
                                </v-btn>

                                <!-- Issues report -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length || (validations.length !== 1)"
                                    :loading="reportTypeLoading('issues')"
                                    value="issues"
                                    title="Issues"
                                >
                                    Issues
                                </v-btn>
                            </v-btn-toggle>
                        </v-toolbar>
                        <!-- Selected validations -->
                        <template v-if="showValidationsList">
                            <v-subheader class="mt-4" style="height: 32px;">
                                Selected Validations
                            </v-subheader>
                            <v-list dense flat subheader class="ml-4" >
                                <v-list-item v-for="(item, i) in branches" :key="i">
                                    <v-list-item-content class="py-0 my-1">
                                        <v-list-item-title v-text="item"></v-list-item-title>
                                    </v-list-item-content>
                                </v-list-item>
                            </v-list>
                        </template>
                    </div>
                    <!-- Report card -->
                    <component
                        v-if="reportIsReadyToBeRendered"
                        class="ml-4 mr-1 mt-2"
                        :is="reportName"
                        :type="reportType"
                        :header="(validations.length > 1) ? 'Validations Comparison' : 'Validation Overview'"
                    />
                </pane>
            </splitpanes>
        </v-col>
    </v-row>
</template>

<script>
    import validationsTree from '@/components/tree/ValidationsTree.vue'
    import comparisonReport from '@/components/reports/Comparison.vue'
    import bestOrLastReport from '@/components/reports/BestOrLast.vue'
    import indicatorReport from '@/components/reports/Indicator.vue'
    import issuesReport from '@/components/reports/Issues.vue'
    import { Splitpanes, Pane } from 'splitpanes'
    import 'splitpanes/dist/splitpanes.css'

    import { mapState, mapGetters } from 'vuex'
    import { alterHistory } from '@/utils/history-management.js'

    export default {
        components: {
            validationsTree,
            Splitpanes, Pane,
            'comparison-report': comparisonReport,
            'best-report': bestOrLastReport,
            'last-report': bestOrLastReport,
            'indicator-report': indicatorReport,
            'issues-report': issuesReport,
        },
        data() {
            return {
                showExpand: false,      // ">" fab button on left pane collapsing
                reportGrouping: 0,
                reportGroups: ['feature', 'component'],
                compareFiltering: 0,
                compareFilters: ['all', 'diff'],
                showPassedPolicy: 0,
                showPassedPolicies: ['show_passed', 'hide_passed']
            }
        },
        computed: {
            ...mapState('tree', ['validations', 'treeLoading']),
            ...mapState('reports', ['showReport', 'reportLoading', 'reportType']),
            ...mapGetters('tree', ['branches']),
            reportName() {
                return `${this.reportType}-report`
            },
            reportType: {
                get() {
                    return this.$store.state.reports.reportType
                },
                set(value) {
                    this.$store.commit('reports/SET_STATE', {reportType: value})
                }
            },
            reportIsReadyToBeRendered() {
                return this.reportType && !this.treeLoading && this.validations.length
            },
            compareButtonName() {
                return (this.validations.length > 1) ? 'Compare Selected' : 'Overview'
            },
            showValidationsList() {
                return (!this.showReport) && this.validations.length
            }
        },
        watch: {
            // Remove report type from store and URL params on validations change
            validations(current, previous) {
                if (previous.length !== 0 && !this._.isEqual(current, previous)) {
                    this.$store.commit('reports/SET_STATE', {'showReport': false})
                    this.reportType = undefined
                    alterHistory('push', {}, ['rtype'])
                }
            },
            reportType(value) {
                if (value) {
                    this.$vuetify.goTo(0)
                }
            }
        },
        methods: {
            reportTypeLoading(type) {
                return this.reportLoading && (type == this.reportType)
            },
            expandPane() {
                this.$refs['split'].panes[0].size = 50
                this.showExpand = false
            },
            reportClick() {
                if (this.reportType == undefined) {
                    this.$store.commit('reports/SET_STATE', {'showReport': false})
                    alterHistory('push', {}, ['rtype'])
                } else {
                    this.$store.commit('reports/SET_STATE', {'showReport': true})
                    alterHistory('push', {rtype: this.reportType})
                }
            }
        },
        created() {
            // get report type from query string
            if (this.$route.query.rtype)
                this.reportType = this.$route.query.rtype
        }
    }
</script>

<style>
    /* DataTable colored zebra */
    .results-table tbody tr:nth-of-type(odd) {
        background-color: rgba(0, 142, 100, .03);
    }
    /* DataTable header font */
    .v-data-table thead th {
        font-size: 14px !important;
    }
    .v-list-item--dense, .v-list--dense .v-list-item {
        min-height: 20px !important;
    }
    /* Panes splitting */
    .splitpanes__pane {
        background-color: #FFFFFF !important;
    }
    .splitpanes__splitter {
        width: 5px !important;
        background-color: #ECEFF1 !important;
        box-shadow: 0px 3px 3px -2px rgba(0, 0, 0, 0.2), 0px 3px 4px 0px rgba(0, 0, 0, 0.34), 0px 1px 8px 0px rgba(0, 0, 0, 0.12) !important;
    }
    .results-table table {
        table-layout: fixed !important;
    }
    .clear-button-badge .v-badge__badge {
        padding: 2px !important;
        height: 14px !important;
        min-width: 14px !important;
        font-size: 9px !important;
        left: calc(100% + 2px) !important;
        top: -9px !important;
    }
</style>
