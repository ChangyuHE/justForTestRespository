<template>
    <v-container fluid>
        <v-btn-toggle
            color="teal" mandatory
            v-model="pageTab"
        >
            <v-btn small class="outlined" value="subfeatures">
                Subfeatures
            </v-btn>
            <v-btn small class="outlined" value="import">
                Import
            </v-btn>
        </v-btn-toggle>

        <v-row justify="center">
            <v-col cols="12" key="1" v-if="pageTab == 'subfeatures'">
                <sub-features/>
            </v-col>
            <v-col cols="10" v-if="pageTab == 'import'">
                <dnd-frame @file-drop="file = $event">
                    <v-file-input
                        label="Select File to import"
                        full-width show-size counter truncate-length="100"
                        class="pt-0" color="blue-grey"
                        v-model="file"
                        :disabled="uploading"
                    ></v-file-input>
                </dnd-frame>

                <v-row>
                    <v-col cols=2>
                        <api-auto-complete
                            class="my-0 ml-0"
                            type="defined"
                            color="blue-grey"
                            model-name="component"
                            v-model="component"
                            :rules="[rules.required(component, 'name')]"
                        >
                        </api-auto-complete>
                    </v-col>

                    <v-icon
                        class="mt-2 pt-2"
                        size="1.25em"
                        title="Request new component creation"
                        @click="requestComponentCreation"
                    >mdi-message-plus-outline</v-icon>
                </v-row>

                <v-btn
                    color="teal" class="white--text mt-2"
                    :loading="uploading"
                    @click="confirmationWindow = true"
                    :disabled="component == undefined || !file"
                >
                    Upload
                </v-btn>

                <!-- Request Item dialog -->
                <request-item-dialog-component v-if="requestItemDialog" model="component" />

                <!-- Verification window -->
                <v-dialog v-if="confirmationWindow" :value="confirmationWindow" max-width="30%">
                    <v-card>
                        <v-card-title>
                            Import confirmation
                        </v-card-title>
                        <v-card-text>
                            <p>Data from the file will be imported to component <b>{{ component.name }}</b></p>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="blue-grey darken-1" text @click="confirmationWindow = false">Close</v-btn>
                            <v-btn color="cyan darken-2" text @click="confirm">Confirm</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>

                <!-- Main import dialog -->
                <v-dialog v-model="errorsDialog" persistent max-width="50%">
                    <v-card>
                        <v-card-title class="gradient-warning-bottom">
                            <span class="headline">Something went wrong during import</span>
                        </v-card-title>

                        <v-card-text>
                            <template v-if="errorsTabs.length">
                                <div class="d-flex">
                                    <v-tabs slider-color="teal darken-4" v-model="tab" style="width: auto">
                                        <v-tab v-for="name in errorsTabs" :key="name" :class="'tab-' + name">
                                            {{ name }}
                                        </v-tab>
                                    </v-tabs>
                                    <span class="d-inline-block text-truncate mt-3 body-1 font-weight-medium">
                                        {{ priorityWarning }}
                                    </span>
                                </div>
                                <v-tabs-items v-model="tab">
                                    <v-tab-item v-for="(edata, priority) in importErrors" :key="priority">
                                        <div v-for="(items, id) in edata" :key="id">
                                            <issue-card v-for="e in items" :key="e.ID"
                                                :error-data="e"
                                                :priority="priority"
                                                :error-code="id" />
                                        </div>
                                    </v-tab-item>
                                </v-tabs-items>
                            </template>
                            <span v-else class="title"><br>No import errors, click IMPORT button</span>
                        </v-card-text>

                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="red" text @click="errorsDialog = false">Close</v-btn>
                            <v-btn color="cyan darken-2" text @click="onUpload" :disabled="uploadFromDialogDisabled">Import</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
            </v-col>

        </v-row>
    </v-container>
</template>

<script>
    import server from '@/server'
    import issueCard from '@/components/IssueCard'
    import subFeatures from '@/views/TestVerifier/SubFeatures'
    import dndFrame from '@/components/helpers/DragAndDropFileInputFrame'
    import apiAutoComplete from '@/components/APIAutoComplete'
    import requestItemDialogComponent from '@/components/RequestItemDialog'
    import { mapGetters, mapState } from 'vuex'

    function getUniqueID(){
        return Math.random().toString(36).slice(2)
    }

    export default {
        components: {
            issueCard,
            subFeatures,
            'dnd-frame': dndFrame,
            apiAutoComplete,
            requestItemDialogComponent
        },
        data() {
            return {
                file: null,
                uploading: false,
                errorsDialog: false,
                priority: {
                    'blocking': ['ERR_MISSING_COLUMNS', 'ERR_WORKBOOK_EXCEPTION'],
                    'high': ['ERR_MISSING_ENTITY'],
                    'medium': [],
                    'low': []
                },
                tab: null,
                pageTab: "subfeatures",
                component: undefined,
                confirmationWindow: false,
            }
        },
        computed: {
            ...mapGetters(['importErrors']),
            ...mapState('request', ['requestItemDialog', 'rules']),
            errorsTabs() {
                let tabs = Object.keys(this.priority)
                tabs.forEach(priority => {
                    if (!(priority in this.importErrors))
                        tabs = tabs.filter(e => e !== priority)
                })
                return tabs
            },
            uploadFromDialogDisabled() {
                return 'blocking' in this.importErrors || 'high' in this.importErrors
            },
            priorityWarning() {
                let priority = this.errorsTabs[this.tab]
                if (priority == 'blocking') {
                    return 'Fix errors in input file to make import possible'
                } else if (priority == 'high') {
                    return 'Create items or make request to remove these errors to make import possible'
                } else if (priority == 'medium') {
                    return 'Possible wrong data warnings, non blocking'
                } else if (priority == 'low') {
                    return 'Non blocking warnings'
                }
                return ''
            },
        },
        methods: {
            confirm() {
                this.confirmationWindow = false
                this.onUpload()
            },
            onUpload() {
                let eData = {}
                Object.keys(this.priority).forEach(p => eData[p] = {})     // blocking: {}, high: {}, ...

                this.uploading = true

                let formData = new FormData()
                formData.append('file', this.file)
                formData.append('component', this.component.id)
                const url = 'test_verifier/import/'
                server
                .post(url, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}})
                .then(response => {
                    console.log('Successfully imported', response)
                    this.$toasted.success('Successfully imported')
                })
                .catch(error => {
                    if (error.response) {           // Request made and server responded out of range of 2xx codes
                        if(error.response.status != 422) {
                            console.log(error.response)
                            let data = JSON.stringify(error.response.data)
                            if (data.length > 200)
                                data = data.slice(0, 200)

                            this.$toasted.global.alert_error_detailed({
                                'header': `Error during import<br>\n
                                           Please copy error data to clipboard and send it to admins<br>\n`,
                                'message': `${error}<br>URL: ${server.defaults.baseURL}/${url}<br>${data}`
                            })
                        } else {
                            let data = error.response.data
                            this.errorsDialog = true

                            // parsed data to fill errors object
                            data.errors.forEach(e => {
                                Object.keys(this.priority).forEach(p => {
                                    if (this.priority[p].includes(e.code)) {
                                        if (!(e.code in eData[p]))
                                            eData[p][e.code] = []
                                        if (e.code in eData[p]) {
                                            eData[p][e.code].push(
                                                {'message': e.message, 'entity': e.entity, 'column': e.column, 'values': e.values, 'ID': getUniqueID()}
                                            )
                                        }
                                    }
                                })
                            })

                            // delete empty priorities
                            Object.keys(eData).forEach(p => {
                                if (Object.keys(eData[p]).length == 0)
                                    delete eData[p]
                            })
                            this.$store.dispatch('setImportErrors', eData)
                        }
                    } else if (error.request) {     // The request was made but no response was received
                        console.log('No response, request:', error.request)
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    } else {
                        console.log('Something happened in setting up the request that triggered an Error:', error.message)
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    }
                })
                .finally(() => { this.uploading = false })
            },
            requestComponentCreation() {
                this.$store.dispatch('request/setRequestDialogState', 'component')
            },
        }
    }
</script>

<style>

</style>