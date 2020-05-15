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
                        <!-- Clear selection button -->
                        <div class="d-flex justify-end">
                            <v-btn x-small fixed color="blue-grey lighten-4" class="mx-n4 mt-2"
                                :disabled="!validations.length"
                                @click="clearSelected"
                            >
                                clear selection
                            </v-btn>
                        </div>
                    </div>
                </pane>
                <!-- Right part -->
                <pane>
                    <div class="ml-4 mr-1 mt-2">
                        <div class="d-flex justify-end">
                            <alert />
                        </div>
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
                                >
                                    Best results report
                                </v-btn>

                                <!-- Comparison report -->
                                <v-btn small class="outlined"
                                    :disabled="!validations.length || (validations.length < 2)"
                                    :loading="reportTypeLoading('compare')"
                                    value="compare"
                                > 
                                    Compare selected
                                </v-btn>
                            </v-btn-toggle>
                        </v-toolbar>

                        <!-- Results card -->
                        <v-card class="my-4 elevation-3" v-if="showResultsTable">
                            <v-card-title class="mb-n6 ml-4">
                                <span v-if="reportType == 'best'">
                                    Best result for validations:
                                </span>
                                <span v-else-if="reportType == 'compare'">
                                    Validations comparison:
                                </span>
                                
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
                            <v-list dense flat class="ml-4">
                                <v-list-item v-for="(item, i) in branches" :key="i">
                                    <v-list-item-content class="py-0 my-1">
                                        <v-list-item-title v-text="item"></v-list-item-title>
                                    </v-list-item-content>
                                </v-list-item>
                            </v-list>
                            <v-divider style="border-color: rgba(0, 0, 0, 0.3); height:2px;"></v-divider>

                            <!-- DataTable -->
                            <v-data-table class="results-table"
                                :headers="headers"
                                :items="items"
                                :search="search"
                                :loading="reportLoading || tableLoading"
                                disable-pagination hide-default-footer multi-sort
                            >
                                <template v-if="reportType == 'best'" v-slot:item.passrate="{ item }">
                                    <v-chip :color="getPassrateColor(item.passrate)" label>{{ item.passrate }}</v-chip>
                                </template>
                                <template v-else-if="reportType == 'compare'" v-slot:item="{ item }">
                                    <tr>
                                        <td v-for="i in item">
                                            <v-chip v-if="STATUSES.includes(i)" :color="getStatusColor(i)" text-color="white" label>{{ i }}</v-chip>
                                            <span v-else>{{ i }}</span>
                                        </td>
                                    </tr>
                                </template>
                            </v-data-table>
                        </v-card>

                        <!-- Selected validations -->
                        <template v-if="!showResultsTable && validations.length">
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

                        <!-- Scrolling to top -->
                        <v-btn
                            v-scroll="onScroll" v-show="showScroll"
                            fab fixed bottom right
                            color="blue-grey lighten-4"
                            @click="toTop"
                        >
                            <v-icon class="d-inline">mdi-apple-keyboard-control</v-icon>
                        </v-btn>
                    </div>
                </pane>
            </splitpanes>
        </v-col>
    </v-row>
</template>

<script>
    import server from '@/server.js'
    import validationsTree from '@/components/ValidationsTree'
    import alert from '@/components/Alert'
    import { Splitpanes, Pane } from 'splitpanes'
    import 'splitpanes/dist/splitpanes.css'

    import { mapState, mapGetters, mapMutations, mapActions } from 'vuex'

	export default {
        components: {
            validationsTree,
            Splitpanes, Pane,
            alert
        },
        data() {
            return {
                showScroll: false,      // "^" button
                showExpand: false,      // ">" button

                // reports
                STATUSES: ['Passed', 'Failed', 'Skipped', 'Error', 'Blocked', 'Canceled'],
                reportType: null,
                reportLoading: false,
                tableLoading: false,
                showResultsTable: false,
                headers: [],
                items: [],
                search: '',
            }
        },
		computed: {
            ...mapState(['validations', 'branches', 'alert']),
        },
        watch: {
            validations() {
                this.showResultsTable = false;
            }
        },
        methods: {
            reportTypeLoading(type) {
                return this.reportLoading && (type == this.reportType);
            },
            expandPane() {
                this.$refs['split'].panes[0].size = 50;
                this.showExpand = false;
            },
            clearSelected() {
                // direct call method from referenced component
                this.$refs['validations-tree'].clearValidations();
            },
            /**
             * Download Excel report generated on backend based on selected validations ids
             */
            reportExcel() {
                let ids = this.validations.join(',');
                this.tableLoading = true;
                const url = `api/report/${this.reportType}/${ids}?report=excel`;
                server
                    .get(url, {responseType: 'blob'})
                    .then(response => {
                        let fileName = 'unknown';
                        const contentDisposition = response.headers['content-disposition'];
                        console.log(contentDisposition)
                        if (contentDisposition) {
                            const m = contentDisposition.match(/filename="(.+)"/);
                            if (m.length == 2)
                                fileName = m[1];
                        }
                        const url = window.URL.createObjectURL(new Blob([response.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', fileName);
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    })
                    .catch(error => {
                        console.log(error);
                        this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                    })
                    .finally(() => this.tableLoading = false);
            },
            reportClick() {
                if (this.reportType == undefined) {
                    this. showResultsTable = false;
                } else {
                    this.reportWeb();
                }
            },
            /**
             * Get report data from backend based on selected validations ids
             */
            reportWeb() {
                let ids = this.validations.join(',');
                this.reportLoading = true;
                const url = `api/report/${this.reportType}/${ids}`;
                server
                    .get(url)
                    .then(response => {
                        // console.log(response.data);
                        this.headers = response.data.headers;
                        this.items = response.data.items;
                    })
                    .catch(error => {
                        console.log(error);
                        this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                    })
                    .finally(() => {
                        this.reportLoading = false;
                        this.showResultsTable = true;
                    });
            },
            onScroll(e) {
                if (typeof window === 'undefined') return;
                const top = window.pageYOffset || e.target.scrollTop || 0;
                this.showScroll = top > 20;
            },
            toTop() {
                this.$vuetify.goTo(0);
            },
            /**
             * Coloring passaretes in report
             */
            getPassrateColor(p) {
                p = Number(p.slice(0, -1));
                if (Number.isNaN(p))
                    p = 0;
                if (p >= 0 && p < 50) return 'red lighten-3'
                else if (p >= 50 && p < 80) return 'yellow lighten-4'
                else if (p >= 80 && p < 100) return 'green lighten-4'
                else return 'green lighten-1'
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
</style>
