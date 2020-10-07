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

        <!-- Mappings selector -->
        <v-col cols="12" class="pb-0">
            <mapping-selector
                :items="mappingItems"
                v-model="mappings"
                @change="onMappingsChange"
                @validation-passed="reportWeb"
            ></mapping-selector>
        </v-col>
        <v-divider class="horizontal-line"></v-divider>

        <v-col class="d-flex mb-1">
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

        <v-col class="d-flex mt-n5">
            <v-spacer></v-spacer>
            <v-card :disabled="reportLoading" flat>
                <v-card-text class="text-body-2 pa-0 ma-0 mr-1">{{ current }} of {{ total }} items shown</v-card-text>
            </v-card>
        </v-col>

        <v-divider class="horizontal-line"></v-divider>

        <!-- DataTable -->
        <v-data-table class="results-table"
            @current-items="onItemFilter"
            :headers="headers"
            :items="items"
            :search="search"
            :loading="reportLoading || excelLoading || extraDataLoading"
            disable-pagination hide-default-footer multi-sort
        >
            <template v-slot:item="{ item }">
                <tr>
                    <td v-for="(cellValue, index) in item" :key="index">
                        <span v-if="index=='f0'"><a class="local-link" @click="openExtraDataDialog(item)">{{ cellValue }}</a></span>
                        <span v-else-if="typeof cellValue === 'object' && cellValue !== null">
                            <v-chip
                                v-if="'status' in cellValue"
                                :color="getStatusColor(cellValue.status)"
                                text-color="white"
                                class="same-width"
                                label
                                @click="!!cellValue.tiId ? openDetailsDialog(cellValue.tiId) : () => null"
                            >{{ cellValue.status }}</v-chip>
                            <v-icon
                                v-if="'status' in cellValue && cellValue.changed"
                                small class="ml-2" title="Update history"
                                @click="openHistoryDialog(cellValue.tiId)"
                            >
                                mdi-clock-outline
                            </v-icon>
                        </span>
                        <span v-else>{{ cellValue }}</span>
                    </td>
                </tr>
            </template>
        </v-data-table>

        <v-dialog v-model="extraDataDialog" max-width="90%">
            <v-card>
                <v-card-title>{{ extraData.item }}</v-card-title>
                <v-card-subtitle class="text-subtitle-1 mt-2">Assets</v-card-subtitle>
                <v-divider></v-divider>
                <v-card-text>
                     <v-simple-table dense>
                        <template v-slot:default>
                            <colgroup>
                                <col class="first-column">
                                <col v-for="datum in extraData.extra" :style="{width: 90 / extraData.extra.length + '%'}" :key="datum.vinfo.validation">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="text-left">Asset</th>
                                    <th v-for="datum in extraData.extra" class="text-left" v-html="formatValidation(datum.vinfo)" :key="datum.vinfo.validation"></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="asset in ['msdk', 'lucas', 'scenario', 'fullsim', 'os']" :key="asset">
                                    <td>{{ asset }}</td>
                                    <td v-for="datum in extraData.extra" class="text-left" :key="datum.vinfo.validation">
                                        <span v-if="'assets' in datum" v-html="formatAssetAsLink(datum.assets[asset])"></span>
                                    </td>
                                </tr>
                            </tbody>
                        </template>
                    </v-simple-table>
                </v-card-text>
                <v-card-subtitle class="text-subtitle-1">Additional parameters</v-card-subtitle>
                <v-divider></v-divider>
                <v-card-text>
                    <v-simple-table dense>
                        <template v-slot:default>
                            <colgroup>
                                <col class="first-column">
                                <col v-for="datum in extraData.extra" :style="{width: 90 / extraData.extra.length + '%'}" :key="datum.vinfo.validation">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="text-left">Parameter</th>
                                    <th v-for="datum in extraData.extra" class="text-left" v-html="formatValidation(datum.vinfo)" :key="datum.vinfo.validation"></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="param in allKeys" :key="param">
                                    <td>{{ param }}</td>
                                    <td v-for="datum in extraData.extra" class="text-left" v-text="formatAdditionalParameter(datum, param)" :key="datum.vinfo.validation"></td>
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

        <!-- Result item overview -->
        <result-item-details
            :resultItemId="selectedResultId"
            v-if="detailsDialog"
            @close="detailsDialog = false"
            @change="reportWeb"
        ></result-item-details>

        <!-- Result item history -->
        <result-history
            v-if="showResultHistory"
            :resultItemId="selectedResultId"
            @close="showResultHistory = false"
        ></result-history>
    </v-card>
</template>

<script>
    import server from '@/server'
    import ResultItemDetails from '@/components/ResultItemDetails'
    import mappingSelector from '@/components/MappingSelector.vue'
    import resultHistory from '@/components/ResultHistory'

    import { mapState, mapGetters } from 'vuex'

    export default {
        components: {
            ResultItemDetails,
            mappingSelector,
            resultHistory
        },
        data() {
            return {
                STATUSES: ['Passed', 'Failed', 'Skipped', 'Error', 'Blocked', 'Canceled'],
                search: '',

                compareFilters: ['all', 'diff'],
                compareFiltering: 0,
                showPassedPolicy: 0,
                showPassedPolicies: ['show_passed', 'hide_passed'],
                showResultHistory: false,
                extraDataLoading: false,
                extraDataDialog: false,
                extraData: {},
                allKeys: [],

                showTooltip: false,
                validationErrors: [],
                mappingItems: [],
                mappings: [],

                // data-table related variables
                filteredHeaders: [],
                filteredItems: [],
                current: 0,

                showHideTestIdStatus: false,
                fileSizeRE: /(\d+)B$/,

                detailsDialog: false,
                selectedResultId: undefined,
            }
        },
        props: {
            type: { type: String, required: true },
            title: { type: String, required: false }
        },
        computed: {
            ...mapState('tree', ['validations']),
            ...mapGetters('tree', ['branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading', 'originalHeaders', 'originalItems', 'total']),
            url() {
                return `api/report/compare/${this.validations}/${this._.map(this.mappings, 'id').join(',')}/`
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
            onItemFilter(items) {
                this.current = items.length
            },
            toggleTestId() {
                this.showHideTestIdStatus = !this.showHideTestIdStatus
                this.reportWeb()
            },
            filterData() {
                if (this._.isUndefined(this.originalHeaders)) {
                    this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })
                }
                this.current = this.total
                this.filteredItems = this._.cloneDeep(this.originalItems)
                this.filteredItems.forEach(item => delete item.f1)
                this.filteredHeaders = this.originalHeaders.filter(header => header.text != 'Test ID')
            },
            isFileSizeParam(name, value) {
                return name == 'file_size' && this.fileSizeRE.test(value)
            },
            formatAssetAsLink(asset) {
                if (typeof asset === 'string' && asset.startsWith("http") && !asset.endsWith("///")) {
                    return `<a href='${asset}' target='_blank'>${asset}</a>`
                }
                return asset
            },
            formatFileSize(value) {
                value.match(this.fileSizeRE)
                let fileSize = parseInt(RegExp.$1)
                fileSize = fileSize.toLocaleString()
                return `${fileSize}\u202FB`
            },
            formatAdditionalParameter(data, parameter) {
                if ('additional_parameters' in data) {
                    const value = data.additional_parameters[parameter]
                    if (this.isFileSizeParam(parameter, value)) {
                        return this.formatFileSize(value)
                    } else {
                        return value
                    }
                }
                return ''
            },
            formatValidation(vinfo) {
                return `${vinfo.validation}<br><small>(${vinfo.platform}, ${vinfo.env}, ${vinfo.os})</small>`
            },
            openExtraDataDialog(item) {
                let testItemIds = []
                let values = Object.values(item)
                const error = "There no validation or test result ids for this test item"

                let lastColumn = this.showHideTestIdStatus ? values.length - 1 : values.length
                for (let i = 4; i <= lastColumn; i++) {
                    let key = `f${i}`
                    let value = item[key]
                    if (typeof value === 'object' && value !== null) {
                        if ('tiId' in value) {
                            testItemIds.push(value['tiId'])
                        } else if ('valId' in value){
                            testItemIds.push(`v${value.valId}`)
                        } else {
                            this.$toasted.global.alert_error(error)
                            return
                        }
                    } else {
                        this.$toasted.global.alert_error(error)
                        return
                    }
                }
                const url = `api/report/extra-data/${testItemIds.join(',')}/`
                this.extraDataLoading = true

                server
                    .get(url)
                    .then(response => {
                        this.extraData = response.data
                        this.extraDataDialog = true
                        this.allKeys = []
                        this.extraData.extra.forEach(data => {
                            if ('additional_parameters' in data) {
                                this.allKeys = this._.union(this.allKeys, Object.keys(data['additional_parameters']))
                            }
                        })
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
            openDetailsDialog(itemId) {
                this.detailsDialog = true
                this.selectedResultId = itemId
            },
            openHistoryDialog(itemId) {
                this.showResultHistory = true
                this.selectedResultId = itemId
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
                        this.filterData()
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
            onMappingsChange() {
                this.filteredHeaders = []
                this.filteredItems = []
                this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })
            },
        },
        mounted() {
            // find appropriate available mappings for our validation
            let url = `api/validations/mappings/?ids=${this.validations[0]}`
            server
                .get(url)
                .then(response => {
                    this.mappingItems = response.data
                    this.reportWeb()
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get available mappings for selected validations', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
        }
    }
</script>

<style>
    .same-width {
        width: 80px;
        display: inline-flex;
        justify-content: center;
    }
    .local-link {
        color: #00f;
        text-decoration: none;
        border-bottom: 1px dashed;
        border-color: rgba(0, 0, 255, 0.3);
    }
    .first-column {
        width: 10%;
    }
</style>