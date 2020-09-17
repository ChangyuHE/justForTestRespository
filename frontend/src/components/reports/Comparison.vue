<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span>{{ reportHeader }}</span>
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
                    <v-btn small v-for="name in compareFilters" :disabled="name == 'diff' && validations.length < 2" :key="name">
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

            <!-- Show/hide Test ID column in the data table -->
            <label class="d-flex align-start mt-4 mr-1 subtitle-1">
                <v-btn-toggle class="ml-2" color="teal">
                    <v-btn small @click="toggleTestId">
                        test id column
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
            :loading="reportLoading || excelLoading || extraDataLoading"
            disable-pagination hide-default-footer multi-sort
        >
            <template v-slot:item="{ item }">
                <tr>
                    <td v-for="(cellValue, index) in item" :key="index">
                        <div v-if="STATUSES.includes(cellValue.status)">
                            <v-chip :color="getStatusColor(cellValue.status)" text-color="white" label>{{ cellValue.status }}</v-chip>
                            <v-hover v-if="cellValue.extra_data == 'yes'" v-slot:default="{ hover }">
                                <v-icon class="ml-2" small :class="{ 'primary--text': hover }" @click="openExtraDataDialog(cellValue.ti_id)">mdi-information</v-icon>
                            </v-hover>
                        </div>
                        <span v-else>{{ cellValue }}</span>
                    </td>
                </tr>
            </template>
        </v-data-table>

        <v-dialog v-model="extraDataDialog" max-width="800">
            <v-card>
                <v-card-title class="headline">
                    {{ this.extraData.validation }}
                        <br>
                    ({{ this.extraData.platform }}, {{ this.extraData.env }}, {{ this.extraData.os }})
                </v-card-title>
                <v-divider></v-divider>
                <v-card-subtitle class="text-subtitle-1 mt-2">
                    <v-chip :color="getStatusColor(this.extraData.status)" text-color="white" small label>{{ this.extraData.status }}</v-chip>&nbsp;&nbsp;&nbsp;{{ this.extraData.item }}
                </v-card-subtitle>
                <v-card-text>
                    <v-simple-table>
                        <template v-slot:default>
                        <thead>
                            <tr>
                                <th class="text-left">Parameter</th>
                                <th class="text-left">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(value, name) in extraData.extra" :key="name">
                                <td>{{ name }}</td>
                                <td>
                                    <template v-if="isFileSizeParam(name, value)">{{ formatFileSize(value) }}</template>
                                    <template v-else>{{ value }}</template>
                                </td>
                            </tr>
                        </tbody>
                        </template>
                    </v-simple-table>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="extraDataDialog = false">Close</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-card>
</template>

<script>
    import server from '@/server'
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
                extraDataLoading: false,
                extraDataDialog: false,
                extraData: {},

                // data-table related variables
                filteredHeaders: [],
                filteredItems: [],
                filtered: false,

                showHideTestIdStatus: false,
                fileSizeRE: /(\d+)B$/,
             }
        },
        props: {
            type: { type: String, required: true },
            title: { type: String, required: false }
        },
        computed: {
            ...mapState('tree', ['validations', 'branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading', 'originalHeaders', 'originalItems']),
            url() {
                return `api/report/compare/${this.validations}`
            },
            reportHeader() {
                return this.title !== undefined ? this.title: 'Validations comparison'
            },
            headers() {
                return this.showHideTestIdStatus ? this.originalHeaders : this.filteredHeaders
            },
            items() {
                return this.showHideTestIdStatus ? this.originalItems : this.filteredItems
            }

        },
        methods: {
            toggleTestId() {
                this.showHideTestIdStatus = !this.showHideTestIdStatus
                this.reportWeb()
            },
            filterData() {
                this.filteredItems = this._.cloneDeep(this.originalItems)
                this.filteredItems.forEach(item => delete item.f1)
                this.filteredHeaders = this.originalHeaders.filter(header => header.text != 'Test ID')
                this.filtered = true
            },
            isFileSizeParam(name, value) {
                return name == 'file_size' && this.fileSizeRE.test(value)
            },
            formatFileSize(value) {
                value.match(this.fileSizeRE)
                let fileSize = parseInt(RegExp.$1)
                fileSize = fileSize.toLocaleString()
                return `${fileSize}\u202FB`
            },
            openExtraDataDialog(itemId) {
                const url = `api/report/extra-data/${itemId}`
                this.extraDataLoading = true

                server
                    .get(url)
                    .then(response => {
                        this.extraData = response.data
                        this.extraDataDialog = true
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during getting of extra data', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.extraDataLoading = false)

            },
            reportExcel() {
                const url = `${this.url}?report=excel&show=${this.compareFilters[this.compareFiltering]},${this.showPassedPolicies[this.showPassedPolicy]}`
                this.$store
                    .dispatch('reports/reportExcel', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" excel report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    });
            },
            changeGrouping() {
                this.reportWeb()
            },
            showHidePassed(){
                this.showPassedPolicy = 1 - this.showPassedPolicy
                this.reportWeb()
            },
            reportWeb() {
                const url = `${this.url}?show=${this.compareFilters[this.compareFiltering]},${this.showPassedPolicies[this.showPassedPolicy]}`
                this.$store
                    .dispatch('reports/reportWeb', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" web report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => {
                        if (!this.filtered) this.filterData()
                    })
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
            this.reportWeb()
        }
    }
</script>

<style>

</style>