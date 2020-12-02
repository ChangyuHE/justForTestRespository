<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span>Issues Report</span>
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

        <v-list dense flat class="mt-4 ml-4">
            <v-list-item v-for="(item, i) in branches" :key="i">
                <v-list-item-content class="py-0 my-1">
                    <v-list-item-title v-html="item"></v-list-item-title>
                </v-list-item-content>
            </v-list-item>
        </v-list>

        <v-divider class="horizontal-line mt-6"></v-divider>

        <v-progress-linear v-if="loading || excelLoading"
            indeterminate
            height="2"
        ></v-progress-linear>

        <template v-if="!_.isEmpty(failedGroups)">
            <v-card-title class="blue-grey--text">
                {{ failedTotal }} Test Item{{ pluralize(failedGroups) }} with status
                <v-chip label small text-color="white" :color="getStatusColor('failed')" class="ml-1">Failed</v-chip>
            </v-card-title>

            <!-- Expansion Panels for Failed TIs -->
            <v-expansion-panels
                multiple
                focusable
            >
                <v-expansion-panel
                    v-for="(testItems, errorFeature) in failedGroups"
                    :key="errorFeature"
                >
                    <v-expansion-panel-header>
                        {{ errorFeature }} ({{ testItems.length }} item{{ pluralize(testItems) }})
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                        <v-data-table
                            :headers="headers"
                            :items="testItems"
                            :search="search"
                            hide-default-footer
                            hide-default-header
                            disable-pagination
                            dense
                        >
                            <template v-slot:item="{ item }">
                                <tr>
                                    <td>{{ item.ti }}</td>
                                    <td>{{ item.err }}</td>
                                </tr>
                            </template>
                        </v-data-table>
                    </v-expansion-panel-content>
                </v-expansion-panel>
            </v-expansion-panels>

            <v-divider class="horizontal-line"></v-divider>
        </template>

        <template v-if="!_.isEmpty(errorGroups)">
            <v-card-title class="blue-grey--text">
                {{ errorTotal }} Test Item{{ pluralize(errorGroups) }} with status
                <v-chip label small text-color="white" :color="getStatusColor('error')" class="ml-1">Error</v-chip>
            </v-card-title>

            <!-- Expansion Panels for Error TIs -->
            <v-expansion-panels
                multiple
                focusable
            >
                <v-expansion-panel
                    v-for="(testItems, errorFeature) in errorGroups"
                    :key="errorFeature"
                >
                    <v-expansion-panel-header>
                        <template v-if="looksLikeHtml(errorFeature)">
                            {{ errorFeature.substring(0, 125) }}…
                        </template>
                        <template v-else>
                            {{ errorFeature }}
                        </template>
                         ({{ testItems.length }} item{{ pluralize(testItems) }})
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                        <v-data-table
                            :headers="headers"
                            :items="testItems"
                            :search="search"
                            hide-default-footer
                            hide-default-header
                            disable-pagination
                            dense
                        >
                            <template v-slot:item="{ item }">
                                <tr>
                                    <td>{{ item.ti }}</td>
                                    <td>
                                        <template v-if="looksLikeHtml(item.err)">
                                            <span class="d-inline-flex">{{ item.err.substring(0, 74) }}…</span>
                                            <v-icon class="d-inline-flex align-center"
                                                @click="showFullResultReason(item.err)"
                                                title="Show full Result reason"
                                            >
                                                mdi-information-outline
                                            </v-icon>
                                        </template>
                                        <template v-else>
                                            {{ item.err }}
                                        </template>
                                    </td>
                                </tr>
                            </template>
                        </v-data-table>

                    </v-expansion-panel-content>
                </v-expansion-panel>
            </v-expansion-panels>
        </template>

        <!-- Result reason html -->
        <v-dialog
            v-if="showResultReasonDialog"
            :value="showResultReasonDialog"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>Result reason</v-card-title>
                <div class="mx-10" v-html="currentResultReason"></div>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="showResultReasonDialog = false">
                        Close
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-card>
</template>

<script>
    import server from '@/server'
    import { mapState, mapGetters } from 'vuex'
    import { getColorFromStatus } from '@/utils/styling.js'

    export default {
        data() {
            return {
                search: '',
                headers: [
                    {text: 'ti', value: 'ti'},
                    {text: 'err', value: 'err'}
                ],
                failedGroups: {},
                errorGroups: {},
                failedTotal: 0,
                errorTotal: 0,
                currentResultReason: "",
                loading: false,
                showResultReasonDialog: false,
            }
        },
        props: {
            type: { type: String, required: true },
        },
        computed: {
            ...mapState('tree', ['validations']),
            ...mapGetters('tree', ['branches']),
            ...mapState('reports', ['excelLoading']),
        },
        methods: {
            getStatusColor(status) {
                return getColorFromStatus(status)
            },
            looksLikeHtml(txt) {
                if (txt.length < 125) return false
                if (!txt.includes('<')) return false
                if (!txt.includes('>')) return false
                return true
            },
            pluralize(array) {
                if (this._.isPlainObject(array)) {
                    return Object.keys(array).length > 1 ? 's' : ''
                } else {
                    return array.length > 1 ? 's' : ''
                }
            },
            showFullResultReason(err) {
                this.currentResultReason = err
                this.showResultReasonDialog = true
            },
            reportExcel() {
                const url = `api/report/issues/${this.validations[0]}/?report=excel`
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
        },
        mounted() {
            this.loading = true
            const url = `api/report/issues/${this.validations[0]}/`
            server
                .get(url)
                .then(response => {
                    this.failedGroups = response.data.failed
                    this.errorGroups = response.data.error

                    for (const error_feature in this.failedGroups) {
                        this.failedTotal += this.failedGroups[error_feature].length
                    }
                    for (const error_feature in this.errorGroups) {
                        this.errorTotal += this.errorGroups[error_feature].length
                    }
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get issues for selected validation', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
                .finally(() => this.loading = false)

        },
    }
</script>
