<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span>Assign Jira Issues</span>
            <v-spacer></v-spacer>

            <!-- Search field -->
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                hide-details
                class="pt-0 mt-0"
            ></v-text-field>
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

        <v-data-table
            :headers="headers"
            :items="items"
            :loading="reportLoading || issuesLoading"
            :search="search"
            disable-pagination hide-default-footer
        >
            <template v-slot:item="{ item: tr }">
                <tr>
                    <td>{{ tr.c0 }}</td>
                    <td>
                        <v-chip
                            :color="getStatusColor(tr.c1)"
                            text-color="white"
                            class="same-width"
                            label
                        >
                            {{ tr.c1 }}
                        </v-chip>
                    </td>
                    <td>
                        <v-autocomplete
                            color="blue-grey"
                            v-model="selectedJiraIssues[tr.c0]"
                            :items="jiraIssues"
                            :menu-props="{closeOnClick: true, closeOnContentClick: true}"
                            dense
                            multiple
                            small-chips
                            return-object
                            search-input.sync="searchInput"
                            @change="addJiraIssue(tr)"
                        >
                            <!-- Show only defect Id in chip -->
                            <template v-slot:selection="{ item, parent }">
                                <v-chip
                                    label
                                    close
                                    small
                                    @click:close="removeJiraIssue(tr, item)"
                                >
                                    {{ item.value }}
                                </v-chip>
                            </template>
                            <template v-slot:default>
                                <v-virtual-scroll
                                    :items="jiraIssues"
                                >
                                </v-virtual-scroll>
                            </template>
                        </v-autocomplete>
                    </td>
                </tr>
            </template>
        </v-data-table>
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
                searchInput: null,
                selectedJiraIssues: {},
                issuesLoading: false,
                jiraIssues: [],
                issueMapping: {},
             }
        },
        props: {
            type: { type: String, required: true },
        },
        computed: {
            ...mapState('tree', ['validations']),
            ...mapGetters('tree', ['branches']),
            ...mapState('reports', ['showReport', 'reportLoading']),
            ...mapState('reports', {'headers': 'originalHeaders', 'items': 'originalItems'}),
        },
        methods: {
            getStatusColor(status) {
                return getColorFromStatus(status)
            },
            reportWeb() {
                const url = `/api/report/defects/${this.validations[0]}/`
                this.$store
                    .dispatch('reports/reportWeb', { url })
                    .then(response => {
                        for (const item of this.items) {
                            const issues = item.c2
                            // Vue cannot detect property addition or deletion.
                            // Since Vue performs the getter/setter conversion
                            // process during instance initialization,
                            // a property must be present in the data object
                            // in order for Vue to convert it and make it reactive.
                            this.$set(this.selectedJiraIssues, item.c0, [])
                            if (issues.length) {
                                for (const issue of issues) {
                                    this.selectedJiraIssues[item.c0].push(this.issueMapping[issue])
                                }
                            }
                        }
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" web report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },
            loadJiraIssues() {
                this.issuesLoading = true
                const url = 'api/jira-issues/'
                server
                    .get(url)
                    .then(response => {
                        for (const issue of response.data) {
                            this.issueMapping[issue.name] = {
                                'text': `[${issue.name}] ${issue.summary}`,
                                'value': issue.name
                            }
                            this.jiraIssues.push(this.issueMapping[issue.name])
                        }
                        this.reportWeb()
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Failed to get list of imported Jira issues')
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.issuesLoading = false)
            },
            removeJiraIssue(testResult, jiraIssue) {
                const itemName = testResult.c0
                this.selectedJiraIssues[itemName] = this.selectedJiraIssues[itemName]
                                                        .filter(el => el.value != jiraIssue.value)
                const testItem = testResult.c3
                const url = `api/report/defects/${this.validations[0]}/${testItem}/remove/${jiraIssue.value}/`

                this.issuesLoading = true
                server
                    .delete(url)
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during removing defect', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => { this.issuesLoading = false })

            },
            addJiraIssue(testResult) {
                const itemName = testResult.c0
                const newIssue = this._.last(this.selectedJiraIssues[itemName]).value

                const testItem = testResult.c3
                const url = `api/report/defects/${this.validations[0]}/${testItem}/add/${newIssue}/`
                this.issuesLoading = true
                server
                    .post(url)
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during assigning new defect', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => { this.issuesLoading = false })
            }
        },
        mounted() {
            this.loadJiraIssues()
        },
    }
</script>

<style scoped>
    .same-width {
        width: 80px;
        display: inline-flex;
        justify-content: center;
    }
</style>
