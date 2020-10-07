<template>
    <div>
        <!-- Result item details -->
        <v-dialog v-if="showDetails" :value="showDetails" class="mt-0 pt-0" persistent no-click-animation max-width="98%">
            <v-card>
                <v-card-title>
                    Result item details
                    <v-icon class="ml-3" title="Update history" @click="showHistory = true">mdi-clock-outline</v-icon>
                    <v-spacer></v-spacer>
                    <v-switch v-model="enableEditing" label="Editing" color="teal darken-1"></v-switch>
                </v-card-title>

                <v-row class="mx-3">
                    <v-col v-for="field of fields.threeOnRow" :key="field" class="py-0" cols="4">
                        <v-text-field
                            color="blue-grey"
                            readonly
                            :append-icon="showEditIcon(field)"
                            @click:append="openEditDialog(field)"
                            class="px-2 py-0"
                            :label="field"
                            :value="fieldValue(field, resultItem)"
                        >
                        </v-text-field>
                    </v-col>
                </v-row>

                <v-row class="mt-11 mx-3">
                    <v-col v-for="asset of fields.assets" :key="asset" class="py-0" cols="6">
                        <v-text-field
                            color="blue-grey"
                            readonly
                            :append-icon="showEditIcon(asset)"
                            @click:append="openEditDialog(asset)"
                            class="px-2 py-0"
                            :label="asset"
                            :value="assetValue(resultItem[asset])"
                        ></v-text-field>
                    </v-col>
                </v-row>

                <!-- Result reason -->
                <v-row class="mx-3">
                    <v-col cols="6">
                        <v-text-field
                            color="blue-grey"
                            readonly
                            append-icon="mdi-information-outline"
                            @click:append="showResultReasonDialog = true"
                            class="px-2 py-0"
                            label="result_reason"
                            :value="resultItem.result_reason"
                        ></v-text-field>
                    </v-col>
                </v-row>

                <!-- Additional parameters -->
                <div class="ml-9 text-subtitle-1 font-weight-light">
                    Additional parameters
                    <v-icon class="ml-2" @click="openEditDialog('additional_parameters')">{{ showEditIcon('additional_parameters') }} </v-icon>
                </div>
                <v-row class="mx-5">
                    <v-simple-table class="px-3 py-0">
                        <template v-slot:default>
                            <thead>
                                <tr>
                                    <th v-for="(_, key) in additional_parameters(resultItem.additional_parameters)" :key="key">
                                        {{ key }}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td v-for="(_, key) in additional_parameters(resultItem.additional_parameters)" :key="key">
                                        {{ additional_parameter(key, resultItem.additional_parameters) }}
                                    </td>
                                </tr>
                            </tbody>
                        </template>
                    </v-simple-table>
                    <v-spacer></v-spacer>
                </v-row>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeResultDetails">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="showConfirmationWindow = true" :disabled="disableResultSaving">
                        Save
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Parameter editing dialog -->
        <v-dialog
            v-if="showEditDialog"
            :value="showEditDialog"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>
                    Edit {{ selectedField }}
                </v-card-title>
                <v-text-field
                    v-if="selectedField == 'additional_parameters'"
                    color="blue-grey"
                    class="my-3 mx-7"
                    :rules="[rules.isValidJson(selectedFieldValue, selectedField)]"
                    :label="selectedField"
                    v-model="selectedFieldValue"
                ></v-text-field>
                <api-auto-complete
                    v-else class="my-3 mx-7"
                    type="defined" color="blue-grey"
                    v-model="selectedFieldValue"
                    :model-name="selectedField"
                    :key="autocompleteKey"
                    :icon="creationIcon(selectedField)"
                    @click:append-outer="showCreationDialog = true"
                ></api-auto-complete>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeEditDialog">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="saveChange">
                        Save
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Dialog of creation new parameter value -->
        <v-dialog
            v-if="showCreationDialog"
            :value="showCreationDialog"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>New {{ selectedField }}</v-card-title>
                <v-text-field
                    v-for="(_, field) in nestedEditableFields(selectedField)" :key="field"
                    color="blue-grey"
                    class="my-3 mx-7"
                    :rules="[rules.required(nestedEditableFields(selectedField)[field]),
                            rules.isValidJson(nestedEditableFields(selectedField)[field], selectedField)]"
                    :label="isAsset ? 'url or asset name' : field"
                    v-model="nestedEditableFields(selectedField)[field]"
                ></v-text-field>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="showCreationDialog = false">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text :disabled="disableCreation(selectedField)" @click="createParameterInstance">
                        Create
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Confirmaton window -->
        <v-dialog
            v-if="showConfirmationWindow"
            :value="showConfirmationWindow"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>Reason of update</v-card-title>

                <!-- Table with changes -->
                <v-simple-table class="my-3 mx-7">
                    <template v-slot:default>
                        <thead>
                            <tr>
                                <th>Field</th>
                                <th>Old value:</th>
                                <th>New value:</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(_, key) in difference(resultItem, resultItemCopy)" :key="key">
                                <td>{{ key }}</td>
                                <template v-if="key != 'additional_parameters'">
                                    <td>{{ descriptiveField(key, resultItemCopy) }}</td>
                                    <td>{{ descriptiveField(key, resultItem) }}</td>
                                </template>
                                <template v-else>
                                    <td v-for="value of [resultItemCopy, resultItem]"
                                        :key="JSON.stringify(value.additional_parameters)"
                                        class="py-0 my-0 align-start"
                                    >
                                        <v-simple-table>
                                            <template v-slot:default>
                                                <thead>
                                                    <tr>
                                                        <th>Parameter:</th>
                                                        <th>Value:</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="(_, key) in additional_parameters(value.additional_parameters)" :key="key">
                                                        <td>
                                                            {{ key }}
                                                        </td>
                                                        <td>
                                                            {{ additional_parameter(key, value.additional_parameters) }}
                                                        </td>
                                                    </tr>

                                                    <!-- Add some empty rows to make tables the same dimention -->
                                                    <template v-if="needToAddRows(value.additional_parameters,
                                                                                  resultItemCopy.additional_parameters,
                                                                                  resultItem.additional_parameters)"
                                                    >
                                                            <tr v-for="i in rowsToInsert(value.additional_parameters,
                                                                                         resultItemCopy.additional_parameters,
                                                                                         resultItem.additional_parameters)"
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
                    </template>
                </v-simple-table>

                <!-- Reason of update -->
                <v-text-field
                    color="blue-grey"
                    class="my-3 mx-7"
                    label="please provide reason of update"
                    :rules="[rules.required(reason), rules.isLongEnough(reason)]"
                    v-model="reason"
                ></v-text-field>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeConfirmationWindow">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text
                        @click="saveResultItem"
                        :disabled="rules.required(reason) != true || rules.isLongEnough(reason) != true"
                    >
                        Update
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- History -->
        <result-history v-if="showHistory" :resultItemId="this.resultItemId" @close="showHistory = false"></result-history>

        <!-- Result reason html -->
        <v-dialog
            v-if="showResultReasonDialog"
            :value="showResultReasonDialog"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>Result reason</v-card-title>
                <div class="mx-10" v-html="resultItem.result_reason"></div>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="showResultReasonDialog = false">
                        Close
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script>
    import server from '@/server'
    import ApiAutoComplete from '@/components/APIAutoComplete'
    import ResultHistory from '@/components/ResultHistory'

    export default {
        components: {
            ApiAutoComplete,
            ResultHistory
        },
        data() {
            return {
                showDetails: false,
                showHistory: false,
                showEditDialog: false,
                showCreationDialog: false,
                showConfirmationWindow: false,
                showResultReasonDialog: false,

                reason: '',
                changes: false,
                resultItem: null,
                resultItemCopy: null,
                enableEditing: false,

                selectedField: null,
                selectedFieldValue: undefined,

                rules: {
                    required(value) {
                        return !!value || 'Required'
                    },
                    isValidJson(value, model) {
                        if ((model == 'additional_parameters' && value != '') || model == 'simics') {
                            try {
                                JSON.parse(value)
                            } catch (exception) {
                                return exception.message
                            }
                        }
                        return true
                    },
                    isLongEnough(value) {
                        if (value.length < 5)
                            return 'At least 5 symbols'
                        return true
                    }
                },

                nestedFields: {
                    assetFields: { url: '' },
                    simicsFields: { data: '' },
                    driverFields: { name: '' },
                },
                fields: {
                    threeOnRow: ['validation', 'driver', 'exec_start',
                                'platform', 'env', 'exec_end',
                                'os', 'status', 'result_key',
                                'component', 'run', 'result_url',
                                'item'],
                    oneOnRow: ['result_reason', 'additional_parameters'],
                    assets: ['scenario_asset', 'msdk_asset',
                            'os_asset', 'lucas_asset',
                            'fulsim_asset', 'simics'],
                },
                canBeCreated: ['scenario_asset', 'simics', 'msdk_asset', 'lucas_asset', 'fulsim_asset', 'driver'],
                editable: ['driver', 'status', 'scenario_asset', 'msdk_asset',
                          'lucas_asset', 'fulsim_asset', 'simics', 'additional_parameters'],
                changeHeaders: ['Field', 'Old value', 'New value'],
                required_additional_parameters: {
                    avg_psnr: '',
                    avg_ssim: '',
                    extreme_psnr: '',
                    extreme_ssim: '',
                    file_size: '',
                    error_features: ''
                },
                // to rerender api-autocomplete
                autocompleteKey: 0,
            }
        },
        props: {
            resultItemId: { type: Number, required: true },
        },
        computed: {
            fieldValue() {
                return (field, resultItem)  => {
                    if (!this._.isObject(resultItem[field])) {
                        return resultItem[field]
                    }
                    // return first field
                    return resultItem[field][Object.keys(resultItem[field])[0]]
                }
            },
            showEditIcon() {
                return field => {
                    if (this.editable.includes(field) && this.enableEditing) {
                        return 'mdi-pencil'
                    } else {
                        return undefined
                    }
                }
            },
            assetValue() {
                return asset => {
                    return !!asset ? (!!asset.data ? asset.data : asset.url) : null
                }
            },
            creationIcon() {
                return field => {
                    return this.canBeCreated.includes(field) ? 'mdi-plus' : undefined
                }
            },
            disableCreation() {
                return model => {
                    for (const value of Object.values(this.nestedEditableFields(model))){
                        // if found empty field value -> disable creation
                        if (!!!value || this.rules.isValidJson(value, model) != true) {
                            return true
                        }
                    }
                    return false
                }
            },
            disableResultSaving() {
                return !this.enableEditing || this._.isEqual(this.resultItem, this.resultItemCopy)
            },
            isAsset() {
                return this.selectedField.includes('asset')
            },
            descriptiveField() {
                return (field, resultItem) => {
                    if (field.includes('asset'))
                        return this.assetValue(resultItem[field])
                    if (field == 'simics')
                        return this.resultItem[field] ? this.resultItem[field]['data'] : ''
                    return this.fieldValue(field, resultItem)
                }
            },
            difference() {
                return (object, base) => {
                    function changes(object, base) {
                        return _.transform(object, function(result, value, key) {
                            if (!_.isEqual(value, base[key])) {
                                result[key] = (_.isObject(value) && _.isObject(base[key])) ? changes(value, base[key]) : value
                            }
                        })
                    }
                    return changes(object, base)
                }
            },
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
            // open
            openEditDialog(field) {
                this.selectedField = field
                this.showEditDialog = true
                this.selectedFieldValue = this.resultItem[this.selectedField]
            },

            // close
            closeResultDetails() {
                this.showDetails = false
                if (this.changes) {
                    this.changes = false
                    this.$emit('change')
                }
                this.$emit('close')
            },
            closeEditDialog() {
                this.showEditDialog = false
                for (let key in this.nestedEditableFields(this.selectedField)) {
                    this.nestedEditableFields(this.selectedField)[key] = ''
                }
            },
            closeConfirmationWindow() {
                this.showConfirmationWindow = false
                this.reason = ''
            },

            // return appropriate object with fields for assets, simics and driver (used to create a new object)
            nestedEditableFields(model) {
                if (model.includes('asset'))
                    return this.nestedFields.assetFields
                if (model == 'simics')
                    return this.nestedFields.simicsFields
                if (model == 'driver')
                    return this.nestedFields.driverFields
            },
            createParameterInstance() {
                let data = Object.assign({}, this.nestedEditableFields(this.selectedField))
                if (this.selectedField == 'simics')
                    try {
                        data.data = JSON.parse(data.data)
                    } catch (exception) {
                        this.$toasted.global.alert_error(exception)
                        return
                    }
                const url = `api/${this.selectedField}/`
                server
                    .post(url, data)
                    .then(response => {
                        // to rerender api autocomplete
                        this.autocompleteKey += 1
                        this.$toasted.success(`New ${this.selectedField} has been successfully created`)
                        this.showCreationDialog = false
                        for (let key in this.nestedEditableFields(this.selectedField)) {
                            this.nestedEditableFields(this.selectedField)[key] = ''
                        }

                        this.selectedFieldValue = response.data

                        // make string from simics.data field (it is JSON field in db so object is returned)
                        if (this.selectedField == 'simics' && this.selectedFieldValue && this.selectedFieldValue.data) {
                            this.selectedFieldValue.data = JSON.stringify(this.selectedFieldValue.data)
                        }
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Error in ${this.selectedField} object creation`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },
            showResultDetails() {
                const url = `api/result/${this.resultItemId}/`
                server
                    .get(url)
                    .then(response => {
                        this.resultItem = response.data

                        // make string from additional_parameters and simics.data fields (it is JSON fields in db so object is returned)
                        if (!!this.resultItem['additional_parameters'])
                            this.resultItem['additional_parameters'] = JSON.stringify(this.resultItem.additional_parameters)
                        if (this.resultItem.simics && this.resultItem.simics.data) {
                            this.resultItem['simics']['data'] = JSON.stringify(this.resultItem.simics.data)
                        }

                        // resultItemCopy is used to track changes
                        this.resultItemCopy = Object.assign({}, this.resultItem)
                        this.enableEditing = false
                        this.showDetails = true
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during retrieving result details', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },

            // save change of 1 result item parameter
            saveChange() {
                // check if additional_parameters contains valid json
                if (this.selectedField == 'additional_parameters' && this.selectedFieldValue != '') {
                    try {
                        const parsedJson = JSON.parse(this.selectedFieldValue)
                    } catch (exception) {
                        this.$toasted.global.alert_error(exception)
                        return
                    }
                }
                this.resultItem[this.selectedField] = this.selectedFieldValue
                this.showEditDialog = false
            },
            saveResultItem() {
                this.changes = true
                let resItemEdited = Object.assign({}, this.resultItem)

                // for all object fields return only id
                for (let key in resItemEdited) {
                    resItemEdited[key] = this._.isObject(resItemEdited[key]) ? resItemEdited[key].id : resItemEdited[key]
                }

                // make object from additional_parameters (JSONfield in backend)
                if (resItemEdited['additional_parameters'] != '') {
                    try {
                        resItemEdited['additional_parameters'] = JSON.parse(resItemEdited['additional_parameters'])
                    } catch (exception) {
                        this.$toasted.global.alert_error(exception)
                        return
                    }
                } else {
                    resItemEdited['additional_parameters'] = null
                }
                resItemEdited['change_reason'] = this.reason
                const url = `api/result/update/${resItemEdited.id}/`
                server
                    .put(url, resItemEdited)
                    .then(response => {
                        Object.assign(this.resultItem, response.data)

                        // make string from additional_parameters and simics.data fields (it is JSON fields in db so object is returned)
                        this.resultItem['additional_parameters'] = JSON.stringify(this.resultItem.additional_parameters)
                        if (this.resultItem.simics && this.resultItem.simics.data) {
                            this.resultItem['simics']['data'] = JSON.stringify(this.resultItem.simics.data)
                        }
                        this.$toasted.success('Result has been edited')
                        this.showEditDialog = false
                        this.reason = ''
                        this.closeResultDetails()
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during requesting edition of this object', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },
        },
        mounted() {
            this.showResultDetails()
        }
    }
</script>