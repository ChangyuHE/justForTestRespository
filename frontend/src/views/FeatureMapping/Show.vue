<template>
    <v-container fluid>
        <v-row justify="center">
            <v-col md="12" lg="8" class="pt-0">
                <v-btn-toggle
                    color="teal" mandatory
                    v-model="showType"
                    @change="showTypeChange"
                >
                    <v-btn small class="outlined" value="show" :loading="loading">
                        Show
                    </v-btn>
                    <v-btn small class="outlined" value="import">
                        Upload
                    </v-btn>
                </v-btn-toggle>
            </v-col>
        </v-row>

        <import-feature-mappings v-if="showType == 'import'" />

        <!-- Mappings data-table -->
        <template v-else>
            <v-row justify="center">
                <v-col md="12" lg="8" class="pt-0">
                    <v-data-table ref="mappingtable" v-if="showMappingTable"
                        dense multi-sort single-select
                        class="row-pointer"
                        :headers="computedMappingHeaders"
                        :items="mappingItems"
                        :items-per-page="5"
                        :search="mappingSearch"
                        :custom-filter="filterWithBool"
                        :footer-props="{'items-per-page-options':[5, 10, 15, -1]}"
                        @click:row="rowClick"
                    >
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                <!-- My/Public toggle -->
                                <v-btn-toggle
                                    color="blue-grey" class="mr-2" mandatory
                                    v-model="mappingType"
                                    @change="mappingTypeChange"
                                >
                                    <v-btn x-small class="outlined" value="my">
                                        my
                                    </v-btn>
                                    <v-btn x-small class="outlined" value="public">
                                        public
                                    </v-btn>
                                </v-btn-toggle>
                                <v-toolbar-title>Feature Mapping Tables</v-toolbar-title>
                                <v-spacer></v-spacer>
                                <v-spacer></v-spacer>
                                <v-text-field
                                    label="Search"
                                    color="blue-grey"
                                    append-icon="mdi-magnify"
                                    single-line hide-details clearable
                                    v-model="mappingSearch"
                                ></v-text-field>

                                <!-- Edit mapping item dialog -->
                                <v-dialog v-model="editMappingItemDialog" max-width="1000px">
                                    <v-card>
                                        <v-card-title>
                                            <span class="headline">Edit mapping</span>
                                        </v-card-title>
                                        <v-card-text>
                                            <v-form v-model="isMapFormValid">
                                            <v-container>
                                                <v-row>
                                                    <!-- Fields controls -->
                                                    <v-col :cols="paramMappingCols(fieldName)" class="pt-0 pb-1" v-for="_, fieldName in showMappingParams" :key="fieldName">
                                                        <v-text-field v-if="fieldName == 'name'"
                                                            class="my-0 pb-1"
                                                            label="Name"
                                                            color="blue-grey"
                                                            hide-details
                                                            v-model="editedMapItem[fieldName]"
                                                        ></v-text-field>
                                                        <v-checkbox v-else-if="fieldName == 'public'"
                                                            class="my-1 pb-1"
                                                            label="Public"
                                                            color="teal darken-1"
                                                            @change="if (!editedMapItem['public']) editedMapItem['official'] = false"
                                                            v-model="editedMapItem[fieldName]"
                                                        ></v-checkbox>
                                                        <v-checkbox v-else-if="fieldName == 'official'"
                                                            class="my-1 pb-1"
                                                            label="Official"
                                                            color="teal darken-1"
                                                            :disabled="!editedMapItem['public']"
                                                            v-model="editedMapItem[fieldName]"
                                                        ></v-checkbox>
                                                        <api-auto-complete v-else
                                                            class="my-0 pb-1"
                                                            type="defined"
                                                            color="blue-grey"
                                                            :model-name="fieldName"
                                                            :rules="[mapRules.required(editedMapItem[fieldName], fieldName)]"
                                                            v-model="editedMapItem[fieldName]"
                                                        ></api-auto-complete>
                                                    </v-col>
                                                </v-row>
                                            </v-container>
                                            </v-form>
                                        </v-card-text>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="blue-grey darken-1" text @click="closeMapDialog">Cancel</v-btn>
                                            <v-btn color="cyan darken-2" text @click="saveMappingItem" :disabled="!isMapFormValid || saveMappingItemDisabled">Save</v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-toolbar>
                        </template>
                        <!-- Actions icons -->
                        <template v-slot:item.actions="{ item }">
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Export to Excel file" class="mr-1" :class="{ 'on-hover': hover }"
                                    @click="exportMapping2Excel(item)"
                                >
                                    mdi-file-excel
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }"  v-if="mappingType == 'my'">
                                <v-icon
                                    small title="Edit" class="mr-1" :class="{ 'on-hover': hover }"
                                    :data-row-map-id="item.id"
                                    @click="editMappingItem(item)"
                                >
                                    mdi-pencil
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }"  v-if="mappingType == 'my'">
                                <v-icon
                                    small title="Delete" :class="{ 'on-hover': hover }"
                                    @click="deleteMappingItem(item)"
                                >
                                    mdi-delete
                                </v-icon>
                            </v-hover>
                        </template>
                    </v-data-table>
                </v-col>
            </v-row>
        </template>

        <!-- Rules data-table -->
        <template>
            <v-row justify="center"  v-if="showRulesTable">
                <v-col  md="12" lg="10">
                    <v-data-table
                        dense multi-sort
                        :search="search"
                        :loading="loading"
                        :headers="computedHeaders"
                        :items="items"
                        :items-per-page="15"
                        :footer-props="{'items-per-page-options':[15, 30, 50, 100, -1]}"
                    >
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                <v-toolbar-title><b>{{ activeRulesTableTitle }}</b> rules
                                    <v-btn icon @click="showRulesTable = false">
                                        <v-icon>mdi-close</v-icon>
                                    </v-btn>
                                </v-toolbar-title>
                                <v-spacer></v-spacer>
                                <v-spacer></v-spacer>
                                <v-text-field
                                    label="Search"
                                    color="blue-grey"
                                    append-icon="mdi-magnify"
                                    single-line hide-details clearable
                                    v-model="search"
                                ></v-text-field>

                                <!-- Create/Edit item dialog -->
                                <v-dialog v-model="editRuleItemDialog" max-width="1000px">
                                    <!-- Add button -->
                                    <template v-slot:activator="{ on, attrs }" v-if="mappingType == 'my'">
                                        <v-btn
                                            color="teal" dark fab small title="New item"
                                            class="mb-2 ml-2"
                                            v-bind="attrs"
                                            v-on="on"
                                        ><v-icon>mdi-plus</v-icon></v-btn>
                                    </template>
                                    <v-card>
                                        <v-card-title>
                                            <span class="headline">{{ formTitle }}</span>
                                        </v-card-title>
                                        <v-card-text>
                                            <v-form v-model="isFormValid">
                                            <v-container>
                                                <v-row>
                                                    <!-- Params selectors -->
                                                    <v-col :cols="paramCols(modelName)" class="pt-0 pb-1" v-for="_, modelName in showParams" :key="modelName">
                                                        <api-auto-complete
                                                            class="my-0 pb-1"
                                                            type="defined"
                                                            color="blue-grey"
                                                            :model-name="modelName"
                                                            :rules="[rules.required(editedItem[modelName], modelName)]"
                                                            v-model="editedItem[modelName]"
                                                        ></api-auto-complete>
                                                    </v-col>
                                                </v-row>
                                            </v-container>
                                            </v-form>
                                        </v-card-text>

                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="blue-grey darken-1" text @click="closeRuleDialog">Cancel</v-btn>
                                            <v-btn color="cyan darken-2" text @click="saveRule" :disabled="!isFormValid || saveRuleDisabled">Save</v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-toolbar>
                        </template>
                        <!-- Actions icons -->
                        <template v-slot:item.actions="{ item }" v-if="mappingType == 'my'">
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Edit rule"
                                    class="mr-1"
                                    :class="{ 'on-hover': hover }"
                                    :data-row-rule-id="item.id"
                                    @click="editRuleItem(item)"
                                >
                                    mdi-pencil
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Delete rule"
                                    :class="{ 'on-hover': hover }"
                                    @click="deleteRuleItem(item)"
                                >
                                    mdi-delete
                                </v-icon>
                            </v-hover>
                        </template>
                    </v-data-table>
                </v-col>
            </v-row>
        </template>
    </v-container>
</template>

<script>
    import server from '@/server'
    import { mapState, mapGetters } from 'vuex'
    import ApiAutoComplete from '@/components/APIAutoComplete'
    import ImportFeatureMappings from './Import'

    // "just edited" animation
    function justEditedAnimation(id, class_name, type) {
        let editedRow = document.querySelector(`[data-row-${type}-id="${id}"]`).closest('tr')
        editedRow.classList.add(class_name)
        setTimeout(() => editedRow.classList.remove(class_name), 2000)
    }

    export default {
        components: {
            ApiAutoComplete, ImportFeatureMappings
        },
        data() {
            return {
                // Show rules data
                showRulesTable: false,
                loading: false,
                showType: 'show',
                showParams: {'milestone': undefined, 'feature': undefined, 'scenario': undefined},
                headers: [],
                items: [],
                search: null,

                // Show mapping data
                mappingType: null,
                activeMapping: null,
                showMappingTable: false,
                mappingItems: [],
                mappingHeaders: [],
                showMappingParams: {'name': undefined, 'platform': undefined, 'os': undefined, 'component': undefined, 'public': undefined, 'official': undefined},
                mappingSearch: null,

                // Edit mappings
                editMappingItemDialog: false,
                editedMapItem: {'name': undefined, 'platform': undefined, 'os': undefined, 'component': undefined, 'public': undefined, 'official': undefined},
                defaultMapItem: {'name': undefined, 'platform': undefined, 'os': undefined, 'component': undefined, 'public': undefined, 'official': undefined},
                mapRules: {
                    required(value, model) {
                        const notEmptyModels = ['name', 'platform', 'os', 'component'];
                        if (notEmptyModels.includes(model))
                            return !!value || 'Required'
                        return true
                    }
                },
                isMapFormValid: null,
                isMapDeleting: false,

                // Edit rules
                editRuleItemDialog: false,
                editedIndex: -1,
                editedItem: {'milestone': undefined, 'feature': undefined, 'scenario': undefined},
                defaultItem: {'milestone': undefined, 'feature': undefined, 'scenario': undefined},
                rules: {
                    required(value, model) {
                        const notEmptyModels = ['milestone', 'feature', 'scenario'];
                        if (notEmptyModels.includes(model))
                            return !!value || 'Required'
                        return true
                    }
                },
                isFormValid: null,
            }
        },
        computed: {
            ...mapState(['userData']),
            // Mappings
            computedMappingHeaders() {
                // show all columns excepth of id one
                return this.mappingHeaders.filter(h => h.value != 'id')
            },
            saveMappingItemDisabled() {
                return this._.isEqual(this.mappingItems[this.editedIndex], this.editedMapItem)
            },
            // Rules
            computedHeaders() {
                // show all columns excepth of id one
                return this.headers.filter(h => !this._.includes(['id', 'mapping'], h.value))
            },
            formTitle() {
                return this.editedIndex === -1 ? 'New Item' : 'Edit Item'
            },
            clearDisabled() {
                return this._.compact(this._.values(this.showParams)).length == 0
            },
            saveRuleDisabled() {
                return this._.isEqual(this.items[this.editedIndex], this.editedItem)
            },
            activeRulesTableTitle() {
                return this.activeMapping.name
            }
        },
        methods: {
            // action on toggling "show"|"import"
            showTypeChange() {
                if (this.showType == 'show')
                    this.getMappings()
                this.showRulesTable = false
            },
            // Get user's or public mapping from DB
            getMappings() {
                this.loading = true
                let url = 'api/feature_mapping/table/'

                if (this.mappingType == 'my') {
                    url = `${url}?owner=${this.userData.id}`
                } else {
                    url = `${url}?public=true`
                }

                server
                    .get(url)
                    .then(response => {
                        this.showMappingTable = true
                        this.mappingHeaders = response.data.headers
                        this.mappingItems = response.data.items
                    })
                    .catch(error => {
                        error.handleGlobally && error.handleGlobally('Error during FeatureMappings data loading', url)
                    })
                    .finally(() => { this.loading = false })
            },
            // Mappings table row click action
            rowClick(item, row) {
                this.loadRulesTable(item)
                row.select(true)
            },
            // filter in Mappings table
            filterWithBool(value, search, item) {
                return value != null && search != null && value.toString().indexOf(search) !== -1
            },
            mappingTypeChange() {
                this.getMappings()
                this.showRulesTable = false
                // flush selected row
                if (this.$refs.mappingtable)
                    this.$refs.mappingtable.selection = []
            },
            // dialog close action
            closeMapDialog() {
                this.editMappingItemDialog = false
                this.$nextTick(() => {
                    this.editedMapItem = Object.assign({}, this.defaultItem)
                    this.editedIndex = -1
                })
            },
            // get columns width according to model
            paramMappingCols(model) {
                if (model == 'name')
                    return 12
                return 4
            },
            // show edit dialog
            editMappingItem(item) {
                this.editedIndex = this.mappingItems.indexOf(item)
                this.editedMapItem = Object.assign({}, item)
                this.editMappingItemDialog = true
            },
            saveMappingItem() {
                // prepare item data to send
                let item = {}
                for (let [k, v] of Object.entries(this.editedMapItem)) {
                    // change auto-complete fields
                    if (typeof(v) === 'object') {
                        this.editedMapItem[k] = v !== null ? v.name : null
                        item[k] = v !== null ? v.id : null
                    // empty fields
                    } else if (v === undefined) {
                        this.editedMapItem[k] = null
                        item[k] = null
                    // text and boolean values
                    } else if (this._.includes(['name', 'official', 'public'], k)) {
                        item[k] = v
                    }
                }

                // back: edit existing one
                const url = `api/feature_mapping/update/${this.editedMapItem.id}/`
                let itemId = this.editedMapItem.id
                server
                    .patch(url, item)
                    .then(response => {
                        this.$toasted.success('Successfully updated')
                        justEditedAnimation(itemId, 'selected-row-ok', 'map')
                        // update DataTable items (front)
                        if (this.editedIndex > -1) {
                            Object.assign(this.mappingItems[this.editedIndex], this.editedMapItem)
                        } else {
                            this.mappingItems.push(this.editedMapItem)
                        }
                        this.closeMapDialog()
                    })
                    .catch(error => {
                        if (error.response) {           // Request made and server responded out of range of 2xx codes
                            if (error.response.status == 400) {
                                let err = error.response.data
                                if (err.non_field_errors == "The fields name, owner, component, platform, os must make a unique set.")
                                    this.$toasted.global.alert_error('You are trying to create existing map')
                            } else {
                                error.handleGlobally && error.handleGlobally('Could not update mapping item', url)
                            }
                        } else if (error.request) {     // The request was made but no response was received
                            console.log('No response, request:', error.request)
                            this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                        } else {
                            console.log('Something happened in setting up the request that triggered an Error:', error.message)
                            this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                        }
                        justEditedAnimation(itemId, 'selected-row-error', 'map')
                        this.closeMapDialog()
                    })
            },
            deleteMappingItem(item) {
                this.isMapDeleting = true
                const index = this.mappingItems.indexOf(item)
                let proceed = confirm('Are you sure you want to delete this item?')
                if (proceed) {
                    const url = `api/feature_mapping/delete/${item.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            // remove from table
                            this.mappingItems.splice(index, 1)
                            this.$toasted.success('Successfully deleted')
                        })
                        .catch(error => {
                            error.handleGlobally && error.handleGlobally('Could not delete mapping item', url)
                        })
                        .finally(() => { this.isMapDeleting = false })
                    }
            },
            exportMapping2Excel(item) {
                const url = `api/feature_mapping/export/${item.id}/`

                this.$store
                    .dispatch('reports/reportExcel', { url })
                    .catch(error => {
                        error.handleGlobally && error.handleGlobally('Could not export mapping', url)
                        justEditedAnimation(itemId, 'selected-row-error', 'map')
                    });
            },
            // RULES
            // show rules table for map by mapping id
            loadRulesTable(item) {
                if (this.isMapDeleting) return

                this.loading = true
                let url = `api/feature_mapping/rules/table/?mapping=${item.id}`

                server
                    .get(url)
                    .then(response => {
                        this.headers = response.data.headers
                        this.items = response.data.items
                        this.showRulesTable = true
                        this.activeMapping = item
                    })
                    .catch(error => {
                        error.handleGlobally && error.handleGlobally('Could not load feature mapping rules', url)
                    })
                    .finally(() => { this.loading = false })
            },
            // show dialog and prepare for editing
            editRuleItem(item) {
                this.editedIndex = this.items.indexOf(item)
                this.editedItem = Object.assign({}, item)
                this.editRuleItemDialog = true
            },
            // Delete item from front and back
            deleteRuleItem(item) {
                const index = this.items.indexOf(item)
                let proceed = confirm('Are you sure you want to delete this item?')
                if (proceed) {
                    // send delete request to backend
                    const url = `api/feature_mapping/rules/delete/${item.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            // remove from table
                            this.items.splice(index, 1)
                            this.$toasted.global.alert_success('Successfully deleted')
                        })
                        .catch(error => {
                            error.handleGlobally && error.handleGlobally('Could not delete item', url)
                        })
                        .finally(() => { this.loading = false })
                    }
            },
            // Create of save edited Rule
            saveRule() {
                // detect create or edit mode
                let toCreate = true

                if (this._.has(this.editedItem, 'id'))
                    toCreate = false

                // prepare item object with ids only
                let item = {}
                for (let [k, v] of Object.entries(this.editedItem)) {
                    if (typeof(v) === 'object') {
                        this.editedItem[k] = v !== null ? v.name : null
                        item[k] = v !== null ? v.id : null
                    } else if (v === undefined) {
                        this.editedItem[k] = null
                        item[k] = null
                    }
                }

                // back: create new item back request ..
                if (toCreate) {
                    item.mapping = this.activeMapping.id
                    const url = `api/feature_mapping/rules/create/`
                    server
                        .post(url, item)
                        .then(response => {
                            this.$toasted.success('Successfully created')

                            // update DataTable items (front)
                            if (this.editedIndex > -1) {
                                Object.assign(this.items[this.editedIndex], this.editedItem)
                            } else {
                                this.items.push(this.editedItem)
                            }
                            this.closeRuleDialog()
                        })
                        .catch(error => {
                            if (error.response) {           // Request made and server responded out of range of 2xx codes
                                if (error.response.status == 400) {
                                    let err = error.response.data
                                    if (err.non_field_errors == "The fields milestone, feature, scenario, mapping must make a unique set.")
                                        this.$toasted.global.alert_error('You are trying to create existing rule')
                                } else {
                                    error.handleGlobally && error.handleGlobally('Could not create item', url)
                                }
                            } else if (error.request) {     // The request was made but no response was received
                                console.log('No response, request:', error.request)
                                this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                            } else {
                                console.log('Something happened in setting up the request that triggered an Error:', error.message)
                                this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                            }
                        })
                } else {
                    // .. edit existing one
                    const url = `api/feature_mapping/rules/update/${this.editedItem.id}/`
                    let itemId = this.editedItem.id
                    server
                        .patch(url, item)
                        .then(response => {
                            console.log(response)
                            this.$toasted.success('Successfully updated')

                            justEditedAnimation(itemId, 'selected-row-ok', 'rule')
                            // update DataTable items (front)
                            if (this.editedIndex > -1) {
                                Object.assign(this.items[this.editedIndex], this.editedItem)
                            } else {
                                this.items.push(this.editedItem)
                            }
                            this.closeRuleDialog()
                        })
                        .catch(error => {
                            if (error.response) {           // Request made and server responded out of range of 2xx codes
                                if (error.response.status == 400) {
                                    let err = error.response.data
                                    if (err.non_field_errors == "The fields milestone, feature, scenario, mapping must make a unique set.")
                                        this.$toasted.global.alert_error('You are trying to create existing rule')
                                } else {
                                    error.handleGlobally && error.handleGlobally('Could not update item', url)
                                }
                            } else if (error.request) {     // The request was made but no response was received
                                console.log('No response, request:', error.request)
                                this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                            } else {
                                console.log('Something happened in setting up the request that triggered an Error:', error.message)
                                this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                            }
                            justEditedAnimation(itemId, 'selected-row-error', 'rule')
                            this.closeRuleDialog()
                        })
                }
            },
            // Flush edit item object and close dialog
            closeRuleDialog() {
                this.editRuleItemDialog = false
                this.$nextTick(() => {
                    this.editedItem = Object.assign({}, this.defaultItem)
                    this.editedIndex = -1
                })
            },
            // get columns width according to model
            paramCols(model) {
                if (model == 'scenario') {
                    return 12
                } else if (model == 'feature') {
                    return 8
                } else {
                    return 4
                }
            }
        },
        mounted() {
            this.getMappings()
        }
    }
</script>

<style scoped>
    button.v-icon.on-hover {
        color: #00897B;
    }
    .row-pointer >>> tbody tr :hover {
        cursor: pointer;
    }
</style>
<style>
    /* just selected "ok" animation */
    .selected-row-ok {
        animation: selected-row-ok 2s 1;
    }
    @keyframes selected-row-ok {
        from {background-color: rgba(166, 219, 206, 0.647)}
        to {background-color: rgba(255, 255, 255, 0)}
    }

    /* just selected "error" animation */
    .selected-row-error {
        animation: selected-row-error 2s 1;
    }
    @keyframes selected-row-error {
        from {background-color: rgba(255, 41, 41, 0.452)}
        to {background-color: rgba(255, 255, 255, 0)}
    }
</style>