<template>
    <v-dialog
            v-if="showHistory"
            :value="showHistory"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>History of result item</v-card-title>
                <v-data-table
                    :expanded.sync="expanded"
                    show-expand
                    single-expand
                    :headers="historyHeaders"
                    :items="history"
                    item-key="date"
                    class="elevation-1"
                >
                    <template v-slot:expanded-item="{ headers, item }">
                        <td :colspan="headers.length" class="px-0">
                        <v-simple-table :colspan="headers.length" dense light>
                            <thead>
                                <tr>
                                    <th>Field</th>
                                    <th>Old value:</th>
                                    <th>New value:</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="change of item.changes" :key="change.field">
                                    <td>{{ change.field }}</td>
                                    <template v-if="change.field != 'additional_parameters'">
                                        <td>{{ change.old }}</td>
                                        <td>{{ change.new }}</td>
                                    </template>
                                    <template v-else>
                                        <td v-for="value of [change.old, change.new]" :key="value" class="py-0 my-0">
                                            <v-simple-table>
                                                <template v-slot:default>
                                                    <thead>
                                                        <tr>
                                                            <th>Parameter:</th>
                                                            <th>Value:</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr v-for="(_, key) in additional_parameters(value)"
                                                            :key="key"
                                                        >
                                                            <td>
                                                                {{ key }}
                                                            </td>
                                                            <td>
                                                                {{ additional_parameter(key, value) }}
                                                            </td>
                                                        </tr>
                                                        <template v-if="needToAddRows(value, change.old, change.new)">
                                                            <tr v-for="i in rowsToInsert(value, change.old, change.new)"
                                                                :key="i"
                                                            >
                                                                <td></td><td></td>
                                                            </tr>
                                                        </template>
                                                    </tbody>
                                                </template>
                                            </v-simple-table>
                                        </td>
                                    </template>
                                </tr>
                            </tbody>
                        </v-simple-table>
                        </td>
                    </template>
                </v-data-table>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeHistoryDialog">
                        Close
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
</template>

<script>
    import server from '@/server'

    export default {
        data() {
            return {
                showHistory: false,
                history: [],
                expanded: [],
                historyHeaders: [
                    { text: 'User', value: 'user' },
                    { text:'Date', value: 'date' },
                    { text:'Reason', value: 'reason' }
                ],
            }
        },
        props: {
            resultItemId: { type: Number, required: true },
        },
        computed: {
            additional_parameters() {
                return params_string => {
                    if (!params_string) {
                        return this.required_additional_parameters
                    }
                    // add required params to params from result item if some of them are missing
                    return this._.assign({}, this.required_additional_parameters, JSON.parse(params_string))
                }
            },
            additional_parameter() {
                return (key, params_string) => {
                    if (!params_string) {
                        return ''
                    }
                    const additional_params = JSON.parse(params_string)
                    return !!additional_params[key] ? additional_params[key] : ''
                }
            },

            // return if we need to insert extra rows into table with additional parameters
            needToAddRows() {
                return (current, old, changed) => {
                    return Object.keys(this.additional_parameters(current)).length ==
                                Math.min(Object.keys(this.additional_parameters(old)).length,
                                         Object.keys(this.additional_parameters(changed)).length)
                }
            },
            rowsToInsert() {
                return (current, old, changed) => {
                    return Math.max(Object.keys(this.additional_parameters(old)).length,
                                    Object.keys(this.additional_parameters(changed)).length) -
                                Object.keys(this.additional_parameters(current)).length
                }
            }
        },
        methods: {
            openHistoryDialog() {
                const url = `api/result/history/${this.resultItemId}/`
                server
                    .get(url)
                    .then(response => {
                        this.history = response.data
                        for (let change of this.history) {
                            change['date'] = this.$options.filters.formatDate(change['date'])
                            for (let diff of change['changes']) {
                                if (diff.field == 'additional_parameters') {
                                    // replace all Nones and single quotes
                                    diff.old = diff.old.replaceAll('\'', '\"')
                                    diff.old = diff.old == 'None' ? null : diff.old
                                    diff.new = diff.new.replaceAll('\'', '\"')
                                    diff.new = diff.new == 'None' ? null : diff.new
                                }
                            }
                        }
                        this.showHistory = true
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during retrieving result update history', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally()
            },
            closeHistoryDialog() {
                this.showHistory = false
                this.$emit('close')
            }
        },
        mounted() {
            this.openHistoryDialog()
        }
    }
</script>