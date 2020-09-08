<template>
    <v-container fluid>
        <v-row class="d-flex justify-center">
            <v-col cols="6" class="pt-0">
                <!-- Import type buttons group -->
                <v-btn-toggle
                    color="teal" mandatory
                    v-model="importType"
                >
                    <v-btn small class="outlined" value="new">
                        New
                    </v-btn>
                    <v-btn small class="outlined" value="existing">
                        Existing
                    </v-btn>
                </v-btn-toggle>

                <!-- File input controller -->
                <dnd-frame @file-drop="file = $event">
                    <v-file-input
                        label="Select File to import"
                        full-width show-size counter truncate-length="100"
                        class="pt-0" color="blue-grey"
                        v-model="file"
                        :disabled="uploading"
                    ></v-file-input>
                </dnd-frame>
                </div>
            </v-col>
        </v-row>

        <v-row class="d-flex justify-center">
            <!-- New validation fields -->
            <template v-if="importType == 'new'">
                <!-- Date picker -->
                <v-col cols="1" class="pt-0 pr-0 d-flex">
                    <v-menu
                        v-model="menu"
                        :close-on-content-click="false"
                        nudge-right="150"
                        transition="scale-transition"
                        min-width="290px"
                    >
                        <template v-slot:activator="{ on }">
                            <v-text-field
                                label="Date"
                                prepend-icon="mdi-calendar"
                                color="blue-grey" readonly clearable
                                v-on="on"
                                v-model="valDate"
                                :disabled="uploading"
                            ></v-text-field>
                        </template>
                        <v-date-picker
                            header-color="blue-grey" color="blue-grey darken-2"
                            v-model="valDate"
                            @input="menu = false" :max="today"
                        ></v-date-picker>
                    </v-menu>
                </v-col>
                <!-- Validation name  -->
                <v-col cols="3" class="pt-0 d-flex">
                    <v-text-field
                        color="blue-grey"
                        label="Validation name"
                        hint="At least 10 symbols"
                        clearable
                        v-model="valName"
                        :disabled="uploading"
                    ></v-text-field>
                </v-col>
                <v-col cols="2" class="pt-0 d-flex">
                    <v-textarea
                        color="blue-grey"
                        label="Notes"
                        hint="Optional field"
                        clearable rows="1"
                        v-model="valNotes"
                        :disabled="uploading"
                    ></v-textarea>
                </v-col>
            </template>

            <!-- Existing validation autocomplete selector -->
            <template v-else>
                <v-col cols="6">
                    <v-autocomplete v-if="importType == 'existing'"
                        label="Validations"
                        color="blue-grey"
                        return-object hide-no-data hide-selected clearable
                        item-text="name"
                        item-value="id"
                        placeholder="Start typing to search available validations or leave empty for new one"
                        prepend-icon="mdi-database-search"
                        :items="items"
                        :loading="isLoading"
                        :search-input.sync="search"
                        :disabled="uploading"
                        v-model="selected"
                    ></v-autocomplete>
                </v-col>
            </template>
        </v-row>

        <v-row class="d-flex justify-center">
            <v-col cols="6" class="pt-0">
                <!-- Main dialog -->
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
                                    <!-- Tab item -->
                                    <v-tab-item v-for="(edata, priority) in importErrors" :key="priority">
                                        <!-- iterating over error codes -->
                                        <div v-for="(items, eCode) in edata" :key="eCode">
                                            <div v-for="(errors, modelName) in items" :key="modelName">
                                                <issue-card v-if="modelName == 'Item' && eCode == 'ERR_MISSING_ENTITY'"
                                                    :error-data="errors"
                                                    :priority="priority"
                                                    :error-code="eCode" />
                                                <issue-card v-for="e in errors" :key="e.ID" v-else
                                                    :error-data="e"
                                                    :priority="priority"
                                                    :error-code="eCode" />
                                            </div>
                                        </div>
                                    </v-tab-item>
                                </v-tabs-items>
                            </template>
                            <span v-else class="title"><br>No import errors, click IMPORT button</span>
                        </v-card-text>

                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="red" text @click="errorsDialog = false">Close</v-btn>
                            <v-btn color="cyan darken-2" text @click="onUploadFromDialog" :disabled="uploadFromDialogDisabled">Import</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
                <v-btn
                    color="teal" class="white--text"
                    :disabled="uploadDisabled"
                    :loading="uploading"
                    @click="onUpload"
                >
                    Upload
                </v-btn>
            </v-col>
        </v-row>
    </v-container>
</template>

<script>
    import server from '@/server'
    import issueCard from '@/components/IssueCard'
    import dndFrame from '@/components/helpers/DragAndDropFileInputFrame'

    import { mapState, mapGetters } from 'vuex'

    function getUniqueID(){
        return Math.random().toString(36).slice(2);
    }

    export default {
        components: {
            issueCard,
            'dnd-frame': dndFrame
        },
        data() {
            return {
                file: null,

                // validations autocomplete selector
                descriptionLimit: 100,
                entries: [],
                isLoading: false,
                selected: {'id': 0},
                search: null,

                // upload
                uploading: false,

                //
                errorsDialog: false,
                priority: {
                    'blocking': ['ERR_EXISTING_VALIDATION', 'ERR_INVALID_VALIDATION_ID', 'ERR_MISSING_COLUMNS', 'ERR_WORKBOOK_EXCEPTION', 'ERR_DATE_FORMAT', 'ERR_AMBIGUOUS_COLUMN'],
                    'high': ['ERR_MISSING_ENTITY'],
                    'medium': [],
                    'low': ['ERR_EXISTING_RUN']
                },
                tab: null,

                importType: 'new',
                valDate: null,
                menu: null,
                valName: '',
                valNotes: '',
            }
        },
        computed: {
            ...mapState(['branches']),
            ...mapGetters(['importErrors']),
            uploadDisabled() {
                if (this.importType == 'existing') {
                    return !(Boolean(this.file) && this.selected && 'id' in this.selected && this.selected.id != 0);
                } else {
                    return !(Boolean(this.file) && this.valDate && this.valName ? this.valName.length >= 10 : false);
                }
            },
            /**
             * Validations Autocomplete items to show
             */
            items() {
                return this.entries.map(entry => {
                    const name = entry.name.length > this.descriptionLimit
                        ? entry.name.slice(0, this.descriptionLimit) + '...'
                        : entry.name
                    return Object.assign({}, entry, { name })
                    })
            },
            // Tabs for import errors dialog
            errorsTabs() {
                let tabs = Object.keys(this.priority);
                tabs.forEach(priority => {
                    if (!(priority in this.importErrors))
                        tabs = tabs.filter(e => e !== priority)
                });
                return tabs;
            },
            uploadFromDialogDisabled() {
                return 'blocking' in this.importErrors || 'high' in this.importErrors
            },
            today() {
                let date = new Date();
                return date.toISOString();
            },
            priorityWarning() {
                let priority = this.errorsTabs[this.tab];
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
        watch: {
            search(val) {
                if (this.items.length > 0) return       // Items have already been loaded
                if (this.isLoading) return              // Items have already been requested
                this.isLoading = true

                // Lazily load input items
                const url = 'api/validations/flat';
                server
                    .get(url)
                    .then(res => {
                        this.entries = res.data
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Failed to validations list (import page)', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => (this.isLoading = false))
            },
        },
        methods: {
            onUploadFromDialog() {
                this.errorsDialog = false;
                let extra = {'force_run': false}
                if ('low' in this.importErrors && 'ERR_EXISTING_RUN' in this.importErrors['low'])
                    extra = {'force_run': true}
                this.onUpload(extra);
            },
            onUpload(extra) {
                let eData = {};
                Object.keys(this.priority).forEach(p => eData[p] = {});     // blocking: {}, high: {}, ...

                this.uploading = true;

                let valId = null;
                if (this.selected && 'id' in this.selected)
                    valId = this.selected.id;

                // FormData filling
                let formData = new FormData();
                formData.append('file', this.file);

                if (this.importType == 'new') {
                    formData.append('validation_name', this.valName);
                    formData.append('validation_date', this.valDate);
                } else {
                    formData.append('validation_id', +valId);
                }
                if ('force_run' in extra)
                    formData.append('force_run', extra['force_run']);

                // post it
                const url = 'api/import/';
                server.post(url, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}
                })
                .then(response => {
                    console.log('Import started in the background', response);
                    this.$toasted.success('Import started in the background.<br>\n' +
                                          'You will be notified by email at the end.', { duration: 4000 })
                })
                .catch(error => {
                    if (error.response) {           // Request made and server responded out of range of 2xx codes
                        if(error.response.status != 422) {
                            console.log(error.response);
                            let data = JSON.stringify(error.response.data);
                            if (data.length > 400)
                                data = data.slice(0, 400)

                            this.$toasted.global.alert_error_detailed({
                                'header': `Error during import<br>\n
                                           Please copy error data to clipboard and send it to admins<br>\n`,
                                'message': `${error}<br>URL: ${server.defaults.baseURL}/${url}<br>${data}`
                            })
                        } else {
                            let data = error.response.data;
                            this.errorsDialog = true;

                            // parsed data to fill errors object
                            data.errors.forEach(e => {
                                Object.keys(this.priority).forEach(p => {
                                    if (this.priority[p].includes(e.code)) {
                                        if (!(e.code in eData[p]))
                                            eData[p][e.code] = {}

                                        if (e.code in eData[p]) {
                                            // errors bound to models
                                            if (e.entity) {
                                                if (!(e.entity.model in eData[p][e.code]))
                                                    eData[p][e.code][e.entity.model] = []

                                                eData[p][e.code][e.entity.model].push(
                                                    {'message': e.message, 'entity': e.entity, 'column': e.column, 'values': e.values, 'ID': getUniqueID()}
                                                )
                                            } else {
                                                // global (no-model) errors
                                                if (!('no-model' in eData[p][e.code]))
                                                    eData[p][e.code]['no-model'] = []

                                                eData[p][e.code]['no-model'].push(
                                                    {'message': e.message, 'entity': e.entity, 'column': e.column, 'values': e.values, 'ID': getUniqueID()}
                                                )
                                            }
                                        }
                                    }
                                });
                            });

                            // delete empty priorities
                            Object.keys(eData).forEach(p => {
                                if (Object.keys(eData[p]).length == 0)
                                    delete eData[p];
                            });
                            this.$store.dispatch('setImportErrors', eData);
                        }
                    } else if (error.request) {     // The request was made but no response was received
                        console.log('No response, request:', error.request);
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    } else {
                        console.log('Something happened in setting up the request that triggered an Error:', error.message);
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    }
                })
                .finally(() => { this.uploading = false })
            }
        }
    }
</script>

<style>
    .v-dialog:not(.v-dialog--fullscreen) {
        top: 10% !important;
        position: absolute !important;
        max-height: 80% !important;
    }
    .gradient-warning-bottom {
        border-bottom: 3px solid transparent;
        border-image-source: linear-gradient(to right, #DD2C00, #FFC107);
        border-image-slice: 1;
    }
    .tab-blocking {
        color: #F44336 !important;  /* red */
    }
    .tab-high {
        color: #F4511E !important;  /* deep-orange darken-1 */
    }
    .tab-medium {
        color: #FF8F00 !important;  /* amber darken-3 */
    }
    .tab-low {
        color: #c48f1e !important;  /* amber darken-3 */
    }
</style>
