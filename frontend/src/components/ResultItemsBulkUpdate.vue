<template>
    <div>
        <!-- Result item details -->
        <v-dialog v-if="showUpdate" :value="showUpdate" class="mt-0 pt-0" persistent no-click-animation max-width="90%">
            <v-card>
                <v-card-title>Update results for {{ resultItemIds.length }} selected items</v-card-title>

                <v-row class="mx-3">
                    <v-col v-for="field of fields.common" :key="field" class="py-0" cols="6">
                        <v-layout>
                            <v-text-field
                                color="blue-grey"
                                readonly
                                append-icon="mdi-pencil"
                                @click:append="openEditDialog(field)"
                                class="px-2 py-0"
                                :label="field"
                                :value="fieldValue(field)"
                            >
                            </v-text-field>
                            <v-btn v-if="oldFieldValues(field).length > 1"
                                color="blue-grey"
                                icon
                                @click="openAllFieldValues(field)"
                            >
                                <v-badge
                                    class="d-flex justify-end clear-button-badge" color="warning"
                                    :content="oldFieldValues(field).length"
                                    :value="oldFieldValues(field).length"
                                    overlap>
                                    <v-icon>mdi-dots-horizontal</v-icon>
                                </v-badge>
                            </v-btn>
                        </v-layout>
                    </v-col>
                </v-row>
                <v-row class="mt-11 mx-3">
                    <v-col v-for="asset of fields.assets" :key="asset" class="py-0" cols="6">
                        <v-layout>
                            <v-text-field
                                color="blue-grey"
                                readonly
                                append-icon="mdi-pencil"
                                @click:append="openEditDialog(asset)"
                                class="px-2 py-0"
                                :label="asset"
                                :value="fieldValue(asset)"
                            ></v-text-field>
                            <v-btn v-if="oldFieldValues(asset).length > 1"
                                color="blue-grey"
                                icon
                                @click="openAllFieldValues(asset)"
                            >
                                <v-badge
                                    class="d-flex justify-end clear-button-badge" color="warning"
                                    :content="oldFieldValues(asset).length"
                                    :value="oldFieldValues(asset).length"
                                    overlap>
                                    <v-icon>mdi-dots-horizontal</v-icon>
                                </v-badge>
                            </v-btn>
                        </v-layout>
                    </v-col>
                </v-row>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeUpdateItems">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="showConfirmationWindow = true">
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
                    :prefix-items="oldFieldValues(selectedField)"
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
                <!-- Reason of update -->
                <v-form v-model="isFormValid">
                    <v-text-field
                        color="blue-grey"
                        class="my-3 mx-7"
                        label="please provide reason of update"
                        :rules="[rules.required(reason), rules.isLongEnough(reason)]"
                        v-model="reason"
                    ></v-text-field>
                </v-form>

                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="closeConfirmationWindow">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text
                        @click="saveResultItem"
                        :disabled="!isFormValid"
                    >
                        Update
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- All values of field -->
        <v-dialog
            v-model="showValuesDialog"
            persistent no-click-animation
            max-width="50%"
        >
            <v-card>
                <v-card-title>All values of {{ selectedField }} field</v-card-title>
                <v-simple-table>
                    <template v-slot:default>
                        <thead>
                            <tr>
                                <th class="text-left">
                                    Item
                                </th>
                                <th class="text-left">
                                    {{ selectedField }}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="result in oldResultItems"
                                :key="result.id"
                            >
                                <td>{{ result.item.name }}</td>
                                <td v-if="isAsset">{{ getAssetValue(selectedField, result) }}</td>
                                <td v-else>{{ getFieldValue(selectedField, result) }}</td>
                            </tr>
                        </tbody>
                    </template>
                </v-simple-table>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text @click="showValuesDialog = false">
                        Close
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script>
    import { EventBus } from '@/event-bus.js'
    import server from '@/server'
    import ApiAutoComplete from '@/components/APIAutoComplete'

    import { mapState } from 'vuex'

    export default {
        components: {
            ApiAutoComplete
        },
        data() {
            return {
                showUpdate: false,
                showValuesDialog: false,
                showEditDialog: false,
                showCreationDialog: false,
                showConfirmationWindow: false,

                isFormValid: true,
                reason: '',
                changes: false,
                resultItems: [],
                oldResultItems: [],

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
                    common: ['driver', 'status'],
                    assets: ['scenario_asset', 'msdk_asset',
                            'lucas_asset',
                            'fulsim_asset', 'simics'],
                },
                canBeCreated: ['scenario_asset', 'simics', 'msdk_asset', 'lucas_asset', 'fulsim_asset', 'driver'],

                // to rerender api-autocomplete
                autocompleteKey: 0,
            }
        },
        props: {
            resultItemIds: { type: Array, required: true },
        },
        computed: {
            ...mapState('tree', ['validations']),
            getFieldValue() {
                return (field, resultItem) => {
                    if (!this._.isObject(resultItem[field])) {
                        return resultItem[field]
                    }
                    // return first field
                    return resultItem[field][Object.keys(resultItem[field])[0]]
                }
            },
            getAssetValue() {
                return (asset, resultItem) => {
                    return !!resultItem[asset] ? (!!resultItem[asset].data ? resultItem[asset].data : resultItem[asset].url) : null
                }
            },
            oldFieldValues() {
                return field => {
                    return this.iterateOverItems(this.oldResultItems, field)
                }
            },
            fieldValue() {
                return field  => {
                    let values =  this.iterateOverItems(this.resultItems, field)
                    return values.length ? values[0] : ''
                }
            },
            iterateOverItems() {
                return (items, field) => {
                    return this._.uniq(items.map((resultItem) => {
                        return this._.includes(this.fields.assets, field) ? this.getAssetValue(field, resultItem) : this.getFieldValue(field, resultItem)
                    }))
                }
            },
            creationIcon() {
                return field => {
                    return this.canBeCreated.includes(field) ? 'mdi-plus' : undefined
                }
            },
            disableCreation() {
                return model => {
                    for (const value of Object.values(this.nestedEditableFields(model))) {
                        // if found empty field value -> disable creation
                        if (!!!value || this.rules.isValidJson(value, model) != true) {
                            return true
                        }
                    }
                    return false
                }
            },
            isAsset() {
                return this._.includes(this.fields.assets, this.selectedField)
            },
        },
        methods: {
            openAllFieldValues(field) {
                this.selectedField = field
                this.showValuesDialog = true
            },
            openEditDialog(field) {
                this.selectedField = field
                this.showEditDialog = true
                this.selectedFieldValue = this.resultItems[0][this.selectedField]
            },
            closeUpdateItems() {
                this.showUpdate = false
                if (this.changes) {
                    this.changes = false
                    this.$emit('change')
                }
                this.$emit('close')
            },
            closeEditDialog() {
                this.showEditDialog = false
            },
            closeConfirmationWindow() {
                this.showConfirmationWindow = false
                this.reason = ''
            },

            // return appropriate object with fields for assets, simics and driver (used to create a new object)
            nestedEditableFields(model) {
                if (model.endsWith("_asset"))
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
            getResultItems() {
                const url = `api/result/?ids__in=${this.resultItemIds.join(',')}`
                server
                    .get(url)
                    .then(response => {
                        this.resultItems = response.data
                        this._.each(this.resultItems, (item) => {
                            if (item.simics && item.simics.data) {
                                item.simics.data = JSON.stringify(item.simics.data)
                            }
                        })
                        // oldResultItems to check existing values
                        this.oldResultItems = this._.cloneDeep(this.resultItems)
                        this.showUpdate = true
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during retrieving resuls', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
            },

            // save change of 1 field for all items
            saveChange() {
                this._.each(this.resultItems, (resultItem) => {
                    resultItem[this.selectedField] = this.selectedFieldValue
                })
                this.showEditDialog = false
            },
            saveResultItem() {
                this.changes = true
                let items = this._.cloneDeep(this.resultItems)
                let data = items.map((item) => {
                    item['change_reason'] = this.reason
                    // for all object fields return only id
                    for (let key in item) {
                        item[key] = this._.isObject(item[key]) ? item[key].id : item[key]
                    }
                    return item
                })
                const url = "api/result/bulk_update/"

                server
                    .put(url, data)
                    .then(response => {
                        let old_statuses = {'Passed': 0, 'Failed': 0, 'Error': 0, 'Blocked': 0, 'Skipped': 0, 'Canceled': 0}
                        for (let item of this.oldResultItems) {
                            old_statuses[item.status.test_status]++
                        }
                        let newStats = {}
                        newStats[this.fieldValue('status')] = this.resultItems.length
                        EventBus.$emit('update-counters', {
                            'old': old_statuses,
                            'new': newStats,
                            'validation': this.validations[0]
                        })
                        this.showEditDialog = false
                        this.reason = ''
                        this.closeUpdateItems()
                        this.$toasted.success('Items have been updated')
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during updating of these items', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => {
                        this.selectedTestItems = []
                        this.reason = ""
                        this.bulkUpdateConfirmDialog = false
                    })
            },
        },
        mounted() {
            this.getResultItems()
        }
    }
</script>