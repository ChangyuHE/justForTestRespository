<template>
    <div>
        <!-- Result item details -->
        <v-dialog v-if="showDetails" :value="showDetails" class="mt-0 pt-0" persistent no-click-animation max-width="98%">
            <v-card>
                <v-card-title>
                    Result item details
                    <v-spacer></v-spacer>
                    <v-switch v-model="enableEditing" disabled label="Editing" color="teal darken-1"></v-switch>
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
                            :value="fieldValue(field)"
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

                <v-row v-for="field in fields.oneOnRow" :key="field" class="mx-5 d-flex">
                    <v-text-field
                        color="blue-grey"
                        readonly
                        :append-icon="showEditIcon(field)"
                        @click:append="openEditDialog(field)"
                        class="px-2 py-0"
                        :label="field"
                        :value="resultItem[field]"
                    ></v-text-field>
                    <v-spacer></v-spacer>
                </v-row>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="saveResultItem" :disabled="disableResultSaving">
                        Save
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="closeResultDetails">
                        Close
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
                    <v-btn color="cyan darken-2" text @click="saveChange">
                        Save
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="closeEditDialog">
                        Close
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
                    v-for="field in Object.keys(nestedEditableFields(selectedField))" :key="field"
                    color="blue-grey"
                    class="my-3 mx-7"
                    :rules="[rules.required(nestedEditableFields(selectedField)[field]),
                            rules.isValidJson(nestedEditableFields(selectedField)[field], selectedField)]"
                    :label="isAsset ? 'url or asset name' : field"
                    v-model="nestedEditableFields(selectedField)[field]"
                ></v-text-field>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text :disabled="disableCreation(selectedField)" @click="createParameterInstance">
                        Create
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="showCreationDialog = false">
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

    export default {
        components: {
            ApiAutoComplete,
        },
        data() {
            return {
                showDetails: false,
                showEditDialog: false,
                showCreationDialog: false,

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

                // to rerender api-autocomplete
                autocompleteKey: 0,
            }
        },
        props: {
            resultItemId: { type: Number, required: true },
        },
        computed: {
            fieldValue() {
                return field => {
                    if (!this._.isObject(this.resultItem[field])) {
                        return this.resultItem[field]
                    }
                    return this.resultItem[field][Object.keys(this.resultItem[field])[0]]
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
                server
                    .get(`api/result/${this.resultItemId}/`)
                    .then(response => {
                        this.resultItem = response.data

                        // make string from additional_parameters and simics.data fields (it is JSON fields in db so object is returned)
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