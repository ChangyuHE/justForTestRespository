<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span>Indicator report</span>
            <v-spacer></v-spacer>
            <!-- Search field -->
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                hide-details
                class="pt-0 mt-0"
            ></v-text-field>

            <v-btn light small fab class="ml-4 elevation-5" @click="reportExcel" :disabled="!mappings.length">
                <v-icon>$excel</v-icon>
            </v-btn>
        </v-card-title>

        <!-- Validations list -->
        <v-col class="d-flex">
            <v-list dense flat class="ml-4">
                <v-list-item v-for="(item, i) in branches" :key="i">
                    <v-list-item-content class="py-0 my-1">
                        <v-list-item-title v-html="item"></v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
            <v-spacer></v-spacer>
        </v-col>

        <v-col>
            <v-btn-toggle
                color="teal"
                mandatory
                v-model="mode"
                @change="onModeChange"
            >
                <v-btn v-for="mode in ['single', 'combined']" :key="mode"
                    :disabled="mappings.length <= 1"
                    :value="mode"
                    small
                >
                    {{ mode }}
                </v-btn>
            </v-btn-toggle>
        </v-col>
        <v-divider class="horizontal-line"></v-divider>

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

        <!-- DataTable(s) -->
        <template v-if="(mode == 'single' && Object.keys(singleItems).length == mappings.length) ||
                        (mode == 'combined' && originalItems.length)">
            <v-data-table v-for="mapping in getMappings()" :key="mapping.id"
                class="results-table-indicator elevation-5 mb-2"
                :headers="getData(mapping.id, 'headers')"
                :items="getData(mapping.id, 'items')"
                :search="search"
                :loading="reportLoading || excelLoading"
                disable-pagination hide-default-footer multi-sort dense
                group-by="milestone"
            >
                <template v-slot:top v-if="mode == 'single'">
                    <v-toolbar color="white" flat dense>
                        <v-toolbar-title>
                            {{ singleItems[mapping.id].obj.codec.name }}
                        </v-toolbar-title>
                    </v-toolbar>
                    <hr>
                </template>
                <template v-slot:header.passrate>
                    Pass Rate
                    <v-tooltip top v-model="showPassRateTooltip">
                        <template v-slot:activator="{ on }">
                            <v-icon size="20" @click="showPassRateTooltip = !showPassRateTooltip">mdi-help-circle</v-icon>
                        </template>
                        Pass Rate = Passed / Total * 100%
                    </v-tooltip>
                </template>
                <template v-slot:header.execrate>
                    Exec Rate
                    <v-tooltip bottom v-model="showExecRateTooltip">
                        <template v-slot:activator="{ on }">
                            <v-icon size="20" @click="showExecRateTooltip = !showExecRateTooltip">mdi-help-circle</v-icon>
                        </template>
                        Exec Rate = (Total - Not Run) / Total * 100%
                    </v-tooltip>
                </template>
                <template v-slot:header.notrun>
                    Not Run
                    <v-tooltip left v-model="showNotRunTooltip">
                        <template v-slot:activator="{ on }">
                            <v-icon size="20" @click="showNotRunTooltip = !showNotRunTooltip">mdi-help-circle</v-icon>
                        </template>
                        Not Run = Blocked + Skipped + Canceled + Not Executed
                    </v-tooltip>
                </template>
                <template v-slot:group="{ group, items }">
                    <tr class="item-group">
                        <td colspan="11">
                            <span class="milestone-header">{{ group }}</span>
                        </td>
                    </tr>
                    <tr v-for="(item, i) in items" :key="JSON.stringify(item)">
                        <td class="pl-8" :key="i + 'feature'">{{ item.feature }}</td>
                        <td :key="i + 'total'">{{ item.total }}</td>
                        <td :key="i + 'passed'">{{ item.passed }}</td>
                        <td :key="i + 'failed'">{{ item.failed }}</td>
                        <td :key="i + 'error'">{{ item.error }}</td>
                        <td :key="i + 'blocked'">{{ item.blocked }}</td>
                        <td :key="i + 'skipped'">{{ item.skipped }}</td>
                        <td :key="i + 'canceled'">{{ item.canceled }}</td>
                        <td :key="i + 'notrun'">{{ item.notrun }}</td>
                        <td :key="i + 'passrate'">{{ item.passrate.toLocaleString("en", {style: "percent"}) }}</td>
                        <td :key="i + 'execrate'">{{ item.execrate.toLocaleString("en", {style: "percent"}) }}</td>
                    </tr>
                </template>
                <template slot="body.append">
                    <tr class="font-weight-bold" :__set="total = getData(mapping.id, 'total')">
                        <td>Total</td>
                        <td>{{ total.total }}</td>
                        <td>{{ total.passed }}</td>
                        <td>{{ total.failed }}</td>
                        <td>{{ total.error }}</td>
                        <td>{{ total.blocked }}</td>
                        <td>{{ total.skipped }}</td>
                        <td>{{ total.canceled }}</td>
                        <td>{{ total.notrun }}</td>
                        <td>{{ total.passrate.toLocaleString("en", {style: "percent"}) }}</td>
                        <td>{{ total.execrate.toLocaleString("en", {style: "percent"}) }}</td>
                    </tr>
                </template>
            </v-data-table>
        </template>
    </v-card>
</template>

<script>
    import Vue from 'vue'
    import server from '@/server'
    import mappingSelector from '@/components/MappingSelector.vue'
    import { mapState, mapGetters } from 'vuex'

    export default {
        components: {
            mappingSelector
        },
        props: {
            type: { type: String, required: true }
        },
        data() {
            return {
                search: '',
                mappingItems: [],
                mappings: [],
                grandTotal: {},
                showTooltip: false,
                validationErrors: [],
                loading: false,
                mode: 'single',
                singleItems: {},
                showPassRateTooltip: false,
                showExecRateTooltip: false,
                showNotRunTooltip: false,
            }
        },
        computed: {
            ...mapState('tree', ['validations']),
            ...mapGetters('tree', ['branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading', 'originalItems', 'originalHeaders']),
            url() {
                return `api/report/indicator/${this.validations[0]}/?fmt_id=${this._.map(this.mappings, 'id').join(',')}&mode=${this.mode}`
            },
        },
        methods: {
            onMappingsChange() {
                // switch mode to single if only one mapping selected
                if (this.mappings.length == 1 && this.mode == 'combined')
                    this.mode = 'single'

                // remove items data on selection change
                if (this.mode == 'single') {
                    this._.each(this.singleItems, (value, key) => {
                        if (!(this._.map(this.mappings, 'id').includes(value.obj.id)))
                            delete this.singleItems[value.obj.id]
                    })
                } else {
                    this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })
                }
            },
            // Return selected mappings for single mode or fake object with id for data-table :key
            getMappings() {
                if (this.mode == 'single') {
                    return this.mappings
                } else {
                    return { id: 'combined_table' }
                }
            },
            getData(id, key) {
                if (this.mode == 'single') {
                    return this.singleItems[id][key]
                } else {
                    if (key == 'headers')
                        return this.originalHeaders
                    else if (key == 'items')
                        return this.originalItems
                    else
                        return this.grandTotal
                }
            },
            onModeChange() {
                this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })
                this.onMappingsChange()
                this.reportWeb()
            },
            reportWeb() {
                if (!this.mappings.length) {
                    this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })
                    return
                }
                // one data-table per mapping
                if (this.mode == 'single') {
                    this.mappings.forEach(mapping => {
                        // get back request only for not stored mappings
                        if (!(mapping.id in this.singleItems))
                            this.$store
                                .dispatch('reports/reportWeb', { url: `api/report/indicator/${this.validations[0]}/?fmt_id=${mapping.id}&mode=${this.mode}` })
                                .then(() => {
                                    let items = [...this.originalItems]
                                    let grandTotal = items.pop()

                                    Vue.set(this.singleItems, mapping.id,
                                        { headers: this.originalHeaders, items: items, total: grandTotal, obj: mapping }
                                    )
                                })
                                .catch(error => {
                                    if (error.handleGlobally) {
                                        error.handleGlobally(`Failed in "${this.type}" web report`, url)
                                    } else {
                                        this.$toasted.global.alert_error(error)
                                    }
                                })
                    })
                // one data-table for all mappigns an once
                } else {
                    this.$store
                        .dispatch('reports/reportWeb', { url: this.url })
                        .then(() => {
                            let items = [...this.originalItems]
                            this.grandTotal = items.pop()
                            this.$store.commit('reports/SET_STATE', { originalItems: items })
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally(`Failed in "${this.type}" web report`, url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                }
            },
            reportExcel() {
                const url = `${this.url}&report=excel`
                this.$store
                    .dispatch('reports/reportExcel', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" excel report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },
        },
        created() {
            this.$store.commit('reports/SET_STATE', { originalItems: [], originalHeaders: [] })

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

<style scoped>
    .milestone-header {
        font-size: 1.0em;
        font-weight: 500;
    }
    .results-table-indicator tr.item-group {
        background-color: rgb(207, 216, 220, 0.5);
    }
</style>
