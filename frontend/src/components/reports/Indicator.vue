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

            <!-- <v-btn light small fab class="ml-4 elevation-5" @click="reportExcel">
                <v-icon>$excel</v-icon>
            </v-btn> -->
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
        </v-col>

        <v-divider class="horizontal-line"></v-divider>

        <!-- Mappings selector -->
        <v-col cols="12" class="d-flex">
            <v-autocomplete
                item-text="name"
                class="py-2"
                color="blue-grey"
                label="Select Feature Mappings to create the report"
                no-data-text="No appropritate mappings found"
                return-object hide-selected clearable multiple small-chips deletable-chips
                :items="mappingItems"
                :loading="loading"
                loader-height="2"
                v-model="mappings"
                :error-messages="validationErrors"
                :menu-props="{closeOnContentClick: true}"
                @change="validate"
            >
                <template v-slot:append-outer>
                    <v-tooltip bottom v-model="showTooltip">
                        <template v-slot:activator="{ on }">
                            <v-icon size="20" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                        </template>
                        <router-link to="/feature-mapping" target="_blank">Mappings</router-link> searched by validation's Platform, OS and Component from all test-items executed during this validation.<br>
                    </v-tooltip>
                </template>

            </v-autocomplete>
        </v-col>

        <!-- DataTable -->
        <v-data-table v-if="items.length"
            class="results-table-indicator"
            :headers="headers"
            :items="items"
            :search="search"
            :loading="reportLoading || excelLoading"
            disable-pagination hide-default-footer multi-sort dense
            group-by="milestone"
        >
            <template v-slot:group="{ group, items }">
                <tr class="item-group">
                    <td colspan="5">
                        <span class="milestone-header">{{ group }}</span>
                    </td>
                </tr>
                <tr v-for="(item, i) in items" :key="JSON.stringify(item)">
                    <td class="pl-8" :key="i + 'feature'">{{ item.feature }}</td>
                    <td :key="i + 'passed'">{{ item.passed }}</td>
                    <td :key="i + 'failed'">{{ item.failed }}</td>
                    <td :key="i + 'blocked'">{{ item.blocked }}</td>
                    <td :key="i + 'executed'">{{ item.executed }}</td>
                </tr>
            </template>
            <template slot="body.append">
                <tr class="font-weight-bold">
                    <td>Total</td>
                    <td>{{ grandTotal.passed }}</td>
                    <td>{{ grandTotal.failed }}</td>
                    <td>{{ grandTotal.blocked }}</td>
                    <td>{{ grandTotal.executed }}</td>
                </tr>
            </template>
        </v-data-table>
    </v-card>
</template>

<script>
    import server from '@/server'
    import { mapState, mapGetters } from 'vuex'

    export default {
        data() {
            return {
                search: '',
                mappingItems: [],
                mappings: [],
                grandTotal: {},
                showTooltip: false,
                validationErrors: [],
                loading: false
            }
        },
        computed: {
            ...mapState('tree', ['validations', 'branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading', 'headers', 'items']),
            url() {
                return 'api/report/indicator/'
            },
        },
        methods: {
            validate(selected) {
                this.validationErrors = []
                this.$store.commit('reports/SET_STATE', {'items': [], 'headers': []})
                if (selected.length > 1) {
                    this.loading = true
                    const url = `api/feature_mapping/conflicts/?ids=${this._.map(selected, 'id')}`
                    server
                        .get(url)
                        .then(response => {
                            if (!response.data) {
                                this.validationErrors.push('Only one feature mapping per codec on platform allowed')
                            } else {
                                this.reportWeb()
                            }
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Failed on feature mappings check', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                        .finally(() => this.loading = false)
                } else {
                    this.reportWeb()
                }
            },
            reportWeb() {
                const url = `${this.url}?validation_id=${this.validations[0]}&fmt_id=${this._.map(this.mappings, 'id').join(',')}`
                if (!this.mappings.length) {
                    this.$store.commit('reports/SET_STATE', {'items': [], 'headers': []})
                    return
                }

                this.$store
                    .dispatch('reports/reportWeb', { url })
                    .then(() => {
                        let items = [...this.items]
                        this.grandTotal = items.pop()
                        this.$store.commit('reports/SET_STATE', {'items': items})
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" web report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },
        },
        created() {
            // to hide selected validations list and flush data-table items data
            this.$store.commit('reports/SET_STATE', {'showReport': true})
            this.$store.commit('reports/SET_STATE', {'items': [], 'headers': []})

            // find appropriate available mappings for our validation
            let url = `api/validations/mappings/?ids=${this.validations.join(',')}`
            server
                .get(url)
                .then(response => {
                    this.mappingItems = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get available mappings for selected validations', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
            this.reportWeb()
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
    .v-tooltip__content {
        pointer-events: initial;
    }
    .v-application .v-tooltip__content a {
        color: rgb(247, 248, 201);
    }
</style>