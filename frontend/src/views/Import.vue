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

                <v-tabs>
                    <!-- URL input controller -->
                    <v-tab>from Comparison View</v-tab>
                        <v-tab-item>
                            <v-text-field
                                prepend-icon="mdi-link-box-variant"
                                label="URL"
                                placeholder="https://gta.intel.com/#/reports/comparison-view.."
                                hint="Paste a link of Comparison View results"
                                v-model="url"
                                :value="url"
                                :disabled="uploading"
                                :rules="[rules.CompViewLinkFormatRules(url)]"
                                @change="onImportDataFill"
                                @click:clear="onImportDataClear"
                                autofocus
                                clearable
                            ></v-text-field>
                        </v-tab-item>
                    <!-- File input controller -->
                    <v-tab>File</v-tab>
                        <v-tab-item>
                            <dnd-frame @file-drop="onFileDrop">
                                 <v-file-input
                                      label="Select File to import"
                                      full-width show-size counter truncate-length="100"
                                      class="pt-0" color="blue-grey"
                                      accept=".xlsx"
                                      v-model="file"
                                      :disabled="uploading"
                                      @change="onImportDataFill"
                                      @click:clear="onImportDataClear"
                                  ></v-file-input>
                            </dnd-frame>
                        </v-tab-item>
                </v-tabs>
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
                        v-model="valName"
                        :disabled="uploading"
                        clearable
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
                                                <issue-card v-if="(modelName == 'Item' ||
                                                                   modelName == 'ResultFeature') &&
                                                                   eCode == 'ERR_MISSING_ENTITY'"
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
                            <!-- Reason of update -->
                            <v-container v-if="importType == 'existing'">
                                <v-form v-model="valid">
                                    <v-text-field
                                        color="blue-grey"
                                        class="mx-7"
                                        label="Please provide reason of update"
                                        :rules="[rules.required(reason), rules.isLongEnough(reason)]"
                                        v-model="reason"
                                    ></v-text-field>
                                </v-form>
                            </v-container>
                            <v-spacer></v-spacer>
                            <v-btn color="red" text @click="errorsDialog = false; reason = ''">Close</v-btn>
                            <v-btn
                                color="cyan darken-2"
                                text @click="onUploadFromDialog"
                                :disabled="uploadFromDialogDisabled"
                            >Import</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
                <v-btn
                    color="teal" class="white--text"
                    :disabled="uploadDisabled"
                    :loading="uploading"
                    @click="onUpload"
                >Upload</v-btn>
            </v-col>
        </v-row>
    </v-container>
</template>

<script>
    import server from '@/server'
    import issueCard from '@/components/IssueCard'
    import dndFrame from '@/components/helpers/DragAndDropFileInputFrame'
    import { mapGetters } from 'vuex'

    import axios from 'axios'

    const GTA_API_USER = process.env.VUE_APP_GTA_API_USER
    const GTA_API_PASSWORD = process.env.VUE_APP_GTA_API_PASSWORD

    function getUniqueID() {
        return Math.random().toString(36).slice(2)
    }

    export default {
        components: {
            issueCard,
            'dnd-frame': dndFrame
        },
        data() {
            return {
                file: null,
                url: null,

                // validations autocomplete selector
                descriptionLimit: 100,
                entries: [],
                isLoading: false,
                selected: {'id': 0},
                search: null,

                rules: {
                    required(value) {
                        return !!value || 'Required'
                    },
                    isLongEnough(value) {
                        if (value.length < 5)
                            return 'At least 5 symbols'
                        return true
                    },
                    CompViewLinkFormatRules(value) {
                        let fullLinkFormat = new RegExp('(?=.*?)(https://gta\\.intel\\.com/#/reports/comparison-view)' +
                            '(.*testRun.+?=\\d+)(.*builds+[%\\d\\w]+name)')
                        if (value && !(fullLinkFormat.test(value))) {
                            return 'Link has incorrect format.\ ' +
                                'Please paste Comparison View results link or fix current one'
                        }
                        return true
                    },
                },
                valid: true,

                // upload
                uploading: false,

                errorsDialog: false,
                priority: {
                    'blocking': [
                        'ERR_EXISTING_VALIDATION',
                        'ERR_INVALID_VALIDATION_ID',
                        'ERR_MISSING_COLUMNS',
                        'ERR_WORKBOOK_EXCEPTION',
                        'ERR_DATE_FORMAT',
                        'ERR_AMBIGUOUS_COLUMN'
                    ],
                    'high': ['ERR_MISSING_ENTITY'],
                    'medium': ['ERR_ITEM_CHANGED'],
                    'low': ['ERR_EXISTING_RUN']
                },
                tab: null,

                importType: 'new',
                valDate: null,
                valDateDefault: null,
                menu: null,
                valName: '',
                valNameDefault: '',
                valNotes: '',
                reason: '',
            }
        },
        computed: {
            ...mapGetters(['importErrors']),
            ...mapGetters(['userName']),

            uploadDisabled() {
                let inputType = null
                if (this.url) {
                    inputType = this.url
                } else {
                    inputType = this.file
                }
                if (this.importType == 'existing') {
                    return !(Boolean(inputType) && this.selected && 'id' in this.selected && this.selected.id !== 0)
                } else {
                    return !(Boolean(inputType) && this.valDate && this.valName ? this.valName.length >= 10 : false)
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
                let tabs = Object.keys(this.priority)
                tabs.forEach(priority => {
                    if (!(priority in this.importErrors))
                        tabs = tabs.filter(e => e !== priority)
                })
                return tabs
            },
            uploadFromDialogDisabled() {
                return 'blocking' in this.importErrors ||
                       'high' in this.importErrors ||
                       (this.importType === 'existing' && !this.valid)
            },
            today() {
                let date = new Date()
                return date.toISOString()
            },
            priorityWarning() {
                let priority = this.errorsTabs[this.tab]
                if (priority == 'blocking') {
                    return 'Fix errors in input file to make import possible'
                } else if (priority == 'high') {
                    return 'Create items or make request to remove these errors to make import possible'
                } else if (priority == 'medium') {
                    return 'Results update detected, confirmation required'
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
                const url = 'api/validations/flat/'
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
            parseReportURL(url) {
                let uri = ''
                let testRun = new RegExp('testRun.+?=(\\d+)')
                let buildVersion = new RegExp('builds\\[.+\\[name]=(\\S+)')
                try {
                    uri = decodeURI(url)
                    // expected output: "..[]=results&complexFilters[0][testRun][]=123456"
                } catch (error) {
                    // catches a malformed URI
                    throw Error(`URL is broken: ${error}`)
                }
                for (let reportSetting of uri.split('&')) {
                    if (reportSetting.match(testRun)) {
                        testRun = RegExp.$1
                    }
                    if (reportSetting.match(buildVersion)) {
                        buildVersion = RegExp.$1
                    }
                }
                // build payload for excel preparing request
                return {
                    'use_api': true,
                    'export_labels': [buildVersion],
                    'custom_fields': [{
                            // Additional custom fields from data for exported results
                            'display_name': 'Custom Errors',
                            'json_path': 'result.custom.tests_errors'
                        },
                        {
                            'display_name': 'Kernel Version',
                            'json_path': 'execution.machine.properties.kernel_version_full.value'
                        }],
                    'query': {
                        'columns': [
                            // The fields which will be included to exported data
                            'itemName', 'args', 'os', 'osFamily', 'platform', 'buildName',
                            'tags', 'milestones', 'reason', 'status', 'submitter',
                            'testSession', 'testRun', 'testRunUrl', 'tpUrl',
                            'vertical', 'mappedComponent', 'component', 'features',
                            'executionType', 'testType', 'resultType', 'resultKey',
                            'gtaxJobsetSessionId', 'gtaxTestRunId', 'gtaxJobId',
                            'sourceInstance', 'rootNamespace',
                            'executionTimeInSeconds',
                            'executionStartTimestamp',
                            'executionEndTimestamp',
                            'bucketName', 'isBest', 'isFirst', 'isLast', 'isWorst'
                        ],
                        'filterGroups': [{
                            'mode': 'DNF',
                            'filters': [{
                                'build': [{
                                    'name': buildVersion
                                }],
                                // The filter tags which control range of included data
                                'tagsAnyOf':[],
                                'tagsExcept': ['notAnIssue', 'obsoleted', 'iteration', 'isolation'],
                                'tagsAllOf':[],
                                'testRun': [testRun],
                            }],
                            'customColumnsFilters': {}
                        }],
                        'globalFilterId': null,
                        'customColumns': [
                            'result.custom.tests_errors',
                            'execution.machine.properties.kernel_version_full.value',
                        ],
                        'compareOn': ['compareIdentifier'],
                        'grouped': true,
                        'skipMissing': false,
                        'diffOnly': false
                    }
                }
            },
            async getFromCompViewLink() {
                function excelExportRequest(payload) {
                    return axios
                          .post('/api/results/v1/results_sql/export',
                              payload,
                              {auth: {username: GTA_API_USER, password: GTA_API_PASSWORD}})
                          .then(response => {
                              return {'data': response.data}
                          })
                }
                function getFileURLRequest(resultKey) {
                    return axios
                          .get(`/api/results/v1/tasks/${resultKey}`,
                              {auth: {username: GTA_API_USER, password: GTA_API_PASSWORD}})
                          .then (response => {
                              if (response.data.status === 'SUCCESS') {
                                  return {'data': response.data, 'url': response.data.result.uri}
                              }
                              if (response.data.status === 'FAILURE') {
                                  return {'data': response.data, 'url': 'FAILURE'}
                              } else {
                                  // return pending state if results still unprepared
                                  return {'data': response.data, 'url': 'PENDING'}
                              }
                          })
                }

               // make queries
               let responseData = '' // common response data of made query
               try {
                  let resultKey = null // key to generated data in database
                  let payload = this.parseReportURL(this.url)

                  await excelExportRequest(payload)
                      .then(response => {
                          resultKey = responseData = response.data
                  })
                  let excelUrl = null // link to remote excel file on Artifactory
                  this.$toasted.success('Retrieving data from GTA...<br>\n' +
                                        'Please wait for a while.', { duration: 12000 })
                  do {
                      await getFileURLRequest(resultKey)
                          .then(response => {
                              responseData = response.data
                              excelUrl = response.url
                      })
                      if (excelUrl === 'FAILURE') {
                          throw 'Link is broken or data does not exist for the results'
                      }
                  } while (excelUrl === 'PENDING')

                  this.$toasted.success('Retrieving completed<br>\n', { duration: 4000 })
                  return excelUrl
               } catch (error) {
                     this.$toasted.global.alert_error_detailed({
                         'header': '<strong>Error during retrieving data from GTA</strong><br>\n\n \
                                   It might be a network issue or GTA API results currently unreachable.\n \
                                   Please copy error data to clipboard if you want to send it to admins<br>\n\n',
                         'message': `<strong>${error}</strong><br>Response Data:<br>${JSON.stringify(responseData)}`
                     })
               }
            },
            onImportDataFill() {
                let inputType = null
                if (this.url) {
                    this.file = null
                    inputType = this.url
                }
                if (this.file) {
                    this.url = null
                    inputType = this.file
                }
                if (inputType !== null) {
                    if (this._.isEmpty(this.valDate)) {
                        let valDate = new Date()
                        if (inputType === this.file) {
                            valDate = new Date(this.file.lastModified)
                        }
                        let month = valDate.getMonth() + 1
                        if (month < 10) {
                            month = `0${month}`
                        }
                        let date = valDate.getDate()
                        if (date < 10) {
                            date = `0${date}`
                        }
                        this.valDateDefault = this.valDate = `${valDate.getFullYear()}-${month}-${date}`
                    }
                    if (this._.isEmpty(this.valName)) {
                        if (inputType === this.file) {
                            let fn = this.file.name
                            this.valName = fn.substring(0, fn.lastIndexOf('.'))
                        } else {
                            this.valName = `${this.valDate}_${this.userName}`
                        }
                        this.valNameDefault = this.valName
                    }
                }
            },
            onImportDataClear() {
                if (this.valName === this.valNameDefault) {
                    this.valName = null
                }
                if (this.valDate === this.valDateDefault) {
                    this.valDate = null
                }
            },
            onFileDrop(event) {
                this.file = event
                this.onImportDataFill()
            },
            onUploadFromDialog() {
                this.errorsDialog = false
                let extra = {
                    'force_run': false,
                    'force_item': false
                    }
                if ('low' in this.importErrors && 'ERR_EXISTING_RUN' in this.importErrors['low'])
                    extra['force_run'] = true
                if ('medium' in this.importErrors && 'ERR_ITEM_CHANGED' in this.importErrors['medium'])
                    extra['force_item'] = true
                this.onUpload(extra)
            },
            async onUpload(extra) {
                let eData = {}
                Object.keys(this.priority).forEach(p => eData[p] = {})     // blocking: {}, high: {}, ...

                this.uploading = true

                let valId = null
                if (this.selected && 'id' in this.selected)
                    valId = this.selected.id

                // FormData filling
                let formData = new FormData()
                let file = this.file

                if (this.url) {
                    file = await this.getFromCompViewLink()
                    formData.append('is_url_import', 'true')
                } else {
                    formData.append('is_url_import', 'false')
                }

                formData.append('file', file)
                if (this.importType === 'new') {
                    formData.append('validation_name', this.valName)
                    formData.append('validation_date', this.valDate)
                } else {
                    formData.append('validation_id', +valId)
                }
                if ('force_run' in extra)
                    formData.append('force_run', extra['force_run'])
                if ('force_item' in extra)
                    formData.append('force_item', extra['force_item'])

                if (this.reason) {
                    formData.append('import_reason', this.reason)
                }

                this.$toasted.success('Starting initial checks of importing data<br>\n' +
                                        'Please wait for a while...', { duration: 12000 })
                const url = 'api/import/'
                server.post(url, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}
                })
                .then(() => {
                    this.$toasted.success('Import started in the background.<br>\n' +
                                          'You will be notified by email at the end.', { duration: 4000 })
                })
                .catch(error => {
                    if (error.response) {           // Request made and server responded out of range of 2xx codes
                        if(error.response.status != 422) {
                            let data = JSON.stringify(error.response.data)
                            if (data.length > 400)
                                data = data.slice(0, 400)

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
                                            eData[p][e.code] = {}

                                        if (e.code in eData[p]) {
                                            // errors bound to models
                                            if (e.entity) {
                                                if (!(e.entity.model in eData[p][e.code]))
                                                    eData[p][e.code][e.entity.model] = []

                                                eData[p][e.code][e.entity.model].push({
                                                   'message': e.message,
                                                   'entity': e.entity,
                                                   'column': e.column,
                                                   'values': e.values,
                                                   'ID': getUniqueID()
                                                })
                                            } else {
                                                // global (no-model) errors
                                                if (!('no-model' in eData[p][e.code]))
                                                    eData[p][e.code]['no-model'] = []

                                                // append amount data from warnings
                                                if (e.message in data.warnings)
                                                    e.message =
                                                        `${e.message} (${data.warnings[e.message]} \
                                                        item${data.warnings[e.message] > 1 ? 's' : ''})`
                                                eData[p][e.code]['no-model'].push({
                                                    'message': e.message,
                                                    'entity': e.entity,
                                                    'column': e.column,
                                                    'values': e.values,
                                                    'ID': getUniqueID(),
                                                    'details': e.details
                                                })
                                            }
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
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    } else {
                        this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                    }
                })
                .finally(() => {
                    this.uploading = false
                    this.reason = ''
                })
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
