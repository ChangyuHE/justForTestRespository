<template>
    <div>
        <v-row class="d-flex justify-center">
            <v-col md="12" lg="8" class="pt-0">
                <!-- File input controller -->
                <dnd-frame @file-drop="file = $event">
                    <v-file-input
                        label="Select feature mapping table Excel file"
                        full-width show-size counter truncate-length="100"
                        class="pt-0 mt-0 mb-n1" color="blue-grey"
                        :disabled="uploading"
                        v-model="file"
                    >
                        <template v-slot:append-outer>
                            <v-tooltip bottom v-model="showTooltip" max-width="700">
                                <template v-slot:activator="{ on }">
                                    <v-icon size="20" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                                </template>
                                <div class="tooltip">
                                    <v-list dense dark color="transparent">
                                        File format:
                                        <v-list-item>
                                            Data must be placed on first workbook sheet. Sheet name doesn't matter.
                                        </v-list-item>
                                        <v-list-item>
                                            <v-list-item-content>
                                                <p>First row is used for headers: choose the names you like, but the meaning must match the mapping below.</p>
                                                <p><b>First column - "milestone", second - "feature", third one - "test scenario" and the last one is "ids".</b></p>
                                            </v-list-item-content>
                                        </v-list-item>
                                    </v-list>
                                </div>
                            </v-tooltip>
                        </template>
                    </v-file-input>
                </dnd-frame>
            </v-col>
        </v-row>

        <!-- Import parameters Platform, Os, Component -->
        <v-row class="d-flex justify-center">
            <v-col md="12" lg="8" class="px-4 pt-0 d-flex">
                <v-text-field
                    color="blue-grey" class="py-1 my-0"
                    clearable
                    label="Mapping name"
                    v-model="mapName"
                ></v-text-field>
            </v-col>
        </v-row>
        <v-row class="d-flex justify-center">
            <v-col md="3" lg="2" class="px-4 pt-0 d-flex" v-for="_, modelName in importBindings" :key="modelName">
                <api-auto-complete v-if="modelName != 'os'"
                    color="blue-grey" class="py-0 my-0"
                    type="defined"
                    :disabled="uploading"
                    :model-name="modelName"
                    v-model="importBindings[modelName]"
                ></api-auto-complete>
                <v-autocomplete v-else
                    class="my-0 py-0"
                    color="blue-grey"
                    label="Os family"
                    item-text="name"
                    return-object hide-no-data hide-selected clearable hide-details
                    :items="familyOses"
                    v-model="importBindings[modelName]"
                ></v-autocomplete>
            </v-col>
        </v-row>
        <v-row class="d-flex justify-center">
            <v-col md="12" lg="8">
                <v-btn
                    color="teal" class="white--text"
                    :disabled="uploadDisabled"
                    :loading="uploading"
                    @click="onUpload"
                >
                    Upload
                </v-btn>
                <v-btn
                    color="blue-grey lighten-1" class="white--text mx-2"
                    :disabled="clearImportDisabled"
                    @click="clearImportSelectors"
                >
                    Clear
                </v-btn>
            </v-col>
        </v-row>
        <!-- Import errors dialog -->
        <v-dialog v-model="errorsDialog" persistent max-width="50%">
            <v-card>
                <v-card-title class="gradient-warning-bottom">
                    <span class="headline">Something went wrong during import</span>
                </v-card-title>

                <v-card-text class="pt-2">
                    <v-list dense color="transparent">
                        <template v-for="error in eData">
                            <v-list-item v-for="(value, key) in error" :key="key+value" class="my-1" style="display: block">
                                <template v-if="_.isArray(value)">
                                    <div class="text-subtitle-1 font-weight-medium">
                                        {{ key }}
                                    </div>
                                    <div v-for="msg in value" :key="msg" class="pl-2 text-body-1">
                                        {{ msg }}
                                    </div>
                                </template>
                                <div v-else class="text-body-1">
                                    {{ key }}: {{  value}}
                                </div>
                            </v-list-item>
                        </template>
                    </v-list>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="blue-grey" text @click="errorsDialog = false">Close</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script>
    import server from '@/server'
    import { mapState } from 'vuex'
    import ApiAutoComplete from '@/components/APIAutoComplete'
    import dndFrame from '@/components/helpers/DragAndDropFileInputFrame'

    export default {
        components: {
            ApiAutoComplete,
            'dnd-frame': dndFrame
        },
        data() {
            return {
                file: null,
                uploading: false,
                showTooltip: false,
                mapName: null,
                importBindings: {'codec': undefined, 'platform': undefined, 'os': undefined, 'component': undefined},
                eData: {},
                errorsDialog: false,
                familyOses: [],
            }
        },
        computed: {
            ...mapState(['userData']),
            uploadDisabled() {
                return !(!!this.file && !!this.mapName && !this._.some(this.importBindings, this._.isEmpty))
            },
            clearImportDisabled() {
                return this._.every(this.importBindings, this._.isEmpty) && !!!this.file && !!!this.mapName
            }
        },
        methods: {
            onUpload() {
                this.uploading = true

                // FormData filling
                let formData = new FormData()
                formData.append('file', this.file)
                formData.append('name', this.mapName)
                formData.append('owner', this.userData.id)

                // add platform, component etc. to formdata
                for (let p in this.importBindings) {
                    if (this._.has(this.importBindings[p], 'id'))
                        formData.append(p, this.importBindings[p].id)
                }

                // post it
                const url = 'api/feature_mapping/import/'
                server.post(url, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}
                })
                .then(response => {
                    console.log('Successfully uploaded', response)
                    let creation_data = response.data.data
                    this.$toasted.success('Successfully uploaded')
                })
                .catch(error => {
                    if (error.response) {           // Request made and server responded out of range of 2xx codes
                        if (error.response.status != 422) {
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
                            this.errorsDialog = true
                            this.eData = error.response.data.errors
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
            clearImportSelectors() {
                this.file = null
                this.mapName = null
                this.importBindings = {'platform': undefined, 'os': undefined, 'component': undefined}
            }
        },
        created() {
            // get family oses for Os selector items
            const url = 'api/os/?group__name=Agnostic'
            server
                .get(url)
                .then(response => {
                    this.familyOses = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get oses', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
        }
    }
</script>

<style scoped>
    .v-tooltip__content > .tooltip {
        pointer-events: auto;
    }
    .v-list-item__content > *:last-child {
        margin-bottom: 0;
    }
</style>