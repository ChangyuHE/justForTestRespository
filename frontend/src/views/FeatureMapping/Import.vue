<template>
    <div>
        <v-row class="d-flex justify-center">
            <v-col cols="6" class="pt-0">
                <!-- File input controller -->
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
                                            <p>First row is used for headers. Select names for you convenience according this mapping:</p>
                                            <p><b>First column - "milestone", second - "feautre" and third one - "test scenario".</b></p>
                                        </v-list-item-content>
                                    </v-list-item>
                                </v-list>
                            </div>
                        </v-tooltip>
                    </template>
                </v-file-input>
            </v-col>
        </v-row>

        <!-- Import parameters Platform, Os, Component -->
        <v-row class="d-flex justify-center">
            <v-col cols="6" class="px-4 pt-0 d-flex">
                <v-text-field
                    color="blue-grey" class="py-0 my-0"
                    clearable
                    label="Mapping name"
                    v-model="mapName"
                ></v-text-field>
            </v-col>
        </v-row>
        <v-row class="d-flex justify-center">
            <v-col cols="2" class="px-4 pt-0 d-flex" v-for="_, modelName in importBindings" :key="modelName">
                <api-auto-complete
                    color="blue-grey" class="py-0 my-0"
                    type="defined"
                    :disabled="uploading"
                    :model-name="modelName"
                    v-model="importBindings[modelName]"
                ></api-auto-complete>
            </v-col>
        </v-row>
        <v-row class="d-flex justify-center">
            <v-col cols="6">
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
                        <v-list-item v-for="(message, title) in eData" :key="title+message">
                            <span class="text-subtitle-1">
                                <b>{{ title }}</b>: {{ message }}
                            </span>
                        </v-list-item>
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

    export default {
        components: {
            ApiAutoComplete
        },
        data() {
            return {
                file: null,
                uploading: false,
                showTooltip: false,
                mapName: null,
                importBindings: {'platform': undefined, 'os': undefined, 'component': undefined},
                eData: {},
                errorsDialog: false,
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
                            let data = error.response.data
                            this.errorsDialog = true
                            this._.each(data.errors, (message, title) => {
                                this.eData[title] = message
                            })
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