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
                                <v-dialog v-model="editMappingItemDialog" max-width="1200px">
                                    <v-card>
                                        <v-card-title>
                                            <span class="headline">Edit mapping</span>
                                        </v-card-title>
                                        <v-card-text>
                                            <v-form v-model="isMapFormValid" @submit.prevent>
                                            <v-container>
                                                <v-row>
                                                    <!-- Fields controls -->
                                                    <v-col :cols="paramMappingCols(fieldName)" class="pt-0 pb-1" v-for="_, fieldName in showMappingParams" :key="fieldName">
                                                        <v-text-field v-if="fieldName == 'name'"
                                                            class="my-0 pb-1"
                                                            label="Name"
                                                            color="blue-grey"
                                                            :rules="[mapRules.required(editedMapItem[fieldName], fieldName), mapRules.counter]"
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
                                                        <v-autocomplete v-else-if="fieldName == 'os'"
                                                            class="my-0 pb-1"
                                                            color="blue-grey"
                                                            label="Os family"
                                                            item-text="name"
                                                            return-object hide-no-data hide-selected clearable hide-details
                                                            :items="familyOses"
                                                            :rules="[mapRules.required(editedMapItem[fieldName], fieldName)]"
                                                            v-model="editedMapItem[fieldName]"
                                                        ></v-autocomplete>
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
                        <template v-slot:item.public="{ item }">
                            <v-icon>
                                <template v-if="item.public">mdi-checkbox-marked</template>
                                <template v-else>mdi-checkbox-blank-outline</template>
                            </v-icon>
                        </template>
                        <template v-slot:item.official="{ item }">
                            <v-icon>
                                <template v-if="item.official">mdi-checkbox-marked</template>
                                <template v-else>mdi-checkbox-blank-outline</template>
                            </v-icon>
                        </template>
                        <!-- Actions icons -->
                        <template v-slot:item.actions="{ item }">
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Export to Excel file" :class="{ 'primary--text': hover }"
                                    @click="exportMapping2Excel(item)"
                                >
                                    mdi-file-excel
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }"  v-if="mappingType == 'my'">
                                <v-icon
                                    small title="Edit" :class="{ 'primary--text': hover }"
                                    :data-row-map-id="item.id"
                                    @click="editMappingItem(item)"
                                >
                                    mdi-pencil
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }"  v-if="mappingType == 'my'">
                                <v-icon
                                    small title="Delete" :class="{ 'primary--text': hover }"
                                    @click="deleteMappingItemDebounced(item)"
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
        <v-row justify="center" v-if="showRulesTable">
            <v-col md="12" lg="10">
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
                                        <v-form v-model="isFormValid" @submit.prevent>
                                        <v-container>
                                            <v-row>
                                                <!-- Params selectors -->
                                                <v-col :cols="paramCols(modelName)" class="pt-0 pb-1" v-for="_, modelName in showParams" :key="modelName">
                                                    <api-auto-complete v-if="modelName != 'ids'"
                                                        class="my-0 pb-1"
                                                        type="defined"
                                                        color="blue-grey"
                                                        :model-name="modelName"
                                                        :rules="[rules.required(editedItem[modelName], modelName)]"
                                                        v-model="editedItem[modelName]"
                                                    ></api-auto-complete>
                                                    <v-combobox v-else
                                                        label="Ids"
                                                        v-model="idItems"
                                                        :delimiters="[' ']"
                                                        single-line
                                                        :hide-no-data="!searchId"
                                                        :search-input.sync="searchId"
                                                        :items="idsToSelect"
                                                        small-chips multiple counter deletable-chips clearable hide-selected
                                                        menu-props="auto"
                                                    >
                                                        <template v-slot:no-data>
                                                            Press <kbd>enter</kbd> or <kbd>space</kbd> to create
                                                            <v-chip>{{ searchId }}</v-chip> id <i>(values with "," or ";" will be splitted to separate ids)</i>
                                                        </template>
                                                    </v-combobox>
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
                    <!-- Item slot -->
                    <template v-slot:item="{ item, index }">
                        <tr>
                            <td>{{ item.milestone.name }}</td>
                            <td>{{ item.feature.name }}</td>
                            <td>{{ item.scenario.name }}</td>
                            <td>
                                <template v-if="item.ids">
                                    <template v-for="(id, i) in ids(item.ids)">
                                        <v-tooltip top :key="id">
                                            <template v-slot:activator="{ on, attrs }">
                                                <v-chip v-show="i < 7"
                                                    small style="margin: 1px"
                                                    v-on="on"
                                                    v-bind="attrs"
                                                    :data-row-id="index"
                                                    :data-hidable="i >= 7 ? true : false"
                                                >
                                                    <span
                                                        class="d-inline-block text-truncate"
                                                        style="max-width: 50px"
                                                    >
                                                        {{ id }}
                                                    </span>
                                                </v-chip>
                                            </template>
                                            <span>{{ id }}</span>
                                        </v-tooltip>
                                    </template>
                                    <v-btn icon v-if="ids(item.ids).length > 5" @click="toggleIds(index)">
                                        <v-icon
                                            color="teal darken-2" small class="toggle-icon" v-text="toggle[index] ? 'mdi-chevron-double-left' : 'mdi-dots-horizontal'"
                                        ></v-icon>
                                    </v-btn>
                                </template>
                            </td>
                            <td>
                                <template v-if="mappingType == 'my'">
                                    <v-hover v-slot:default="{ hover }">
                                        <v-icon
                                            small title="Edit rule"
                                            class="mr-1"
                                            :class="{ 'primary--text': hover }"
                                            :data-row-rule-id="item.id"
                                            @click="editRuleItem(item)"
                                        >
                                            mdi-pencil
                                        </v-icon>
                                    </v-hover>
                                    <v-hover v-slot:default="{ hover }">
                                        <v-icon
                                            small title="Delete rule"
                                            :class="{ 'primary--text': hover }"
                                            @click="deleteRuleItem(item)"
                                        >
                                            mdi-delete
                                        </v-icon>
                                    </v-hover>
                                </template>
                            </td>
                        </tr>
                    </template>
                </v-data-table>
            </v-col>
        </v-row>
    </v-container>
</template>

<script>
    import Vue from 'vue'
    import { mapState, mapGetters } from 'vuex'
    import server from '@/server'
    import ApiAutoComplete from '@/components/APIAutoComplete'
    import ImportFeatureMappings from './Import'
    import { justEditedAnimation } from '@/utils/data-table-animation.js'

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
                showParams: {'milestone': undefined, 'feature': undefined, 'scenario': undefined, 'ids': undefined},
                headers: [],
                items: [],
                search: null,
                toggle: {},
                searchId: null,
                idItems: [],
                idsToSelect: [],
                familyOses: [],

                // Show mapping data
                mappingType: null,
                activeMapping: null,
                showMappingTable: false,
                mappingItems: [],
                mappingHeaders: [],
                showMappingParams: {'name': undefined, 'codec': undefined, 'platform': undefined, 'os': undefined, 'component': undefined, 'public': undefined, 'official': undefined},
                mappingSearch: null,

                // Edit mappings
                editMappingItemDialog: false,
                editedMapItem: {},
                defaultMapItem: {},
                mapRules: {
                    required: (value, model) => {
                        const notEmptyModels = ['name', 'codec', 'platform', 'os', 'component']
                        if (notEmptyModels.includes(model))
                            return !!value || 'Required'
                        return true
                    },
                    counter: value => (value && value.length < 256) || 'Name must be less than 256 symbols'
                },
                isMapFormValid: null,
                isMapDeleting: false,

                // Edit rules
                editRuleItemDialog: false,
                editedIndex: -1,
                editedItem: {},
                defaultItem: {},
                rules: {
                    required(value, model) {
                        const notEmptyModels = ['milestone', 'feature', 'scenario']
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
                let bodyOk = this._.isEqual(this.items[this.editedIndex], this.editedItem)
                let idsOk = true
                if (!this._.isEmpty(this.idItems) || !this._.isEmpty(this.editedItem.ids))
                    idsOk = this._.join(this.idItems, ',') == this.editedItem.ids
                return bodyOk && idsOk
            },
            activeRulesTableTitle() {
                return this.activeMapping.name
            }
        },
        watch: {
            idItems(values, previous) {
                if (values.length === previous.length) return
                // map all items in values, split by , or ; and return back splitted ones, remove emtpy and end with by uniq
                values = this._.uniq(this._.reject(this._.flatMap(values, v => v.split(/[,;]/)), this._.isEmpty))
                this.idItems = values
                values.map(v => this.idsToSelect.push(v))
            },
            editMappingItemDialog(val) {
                val || this.closeMapDialog()
            },
            editRuleItemDialog(val) {
                val || this.closeRuleDialog()
            },
        },
        methods: {
            filter(item, queryText, itemText) {
                if (item.header) return false

                const hasValue = val => val != null ? val : ''

                const text = hasValue(itemText)
                const query = hasValue(queryText)

                return text.toString()
                    .toLowerCase()
                    .indexOf(query.toString().toLowerCase()) > -1
            },
            ids(idsString) {
                if (idsString)
                    return idsString.split(',')
                return []
            },
            toggleIds(index) {
                if (!this.toggle[index]) {
                    document.querySelectorAll(`[data-row-id="${index}"][data-hidable=true]`).forEach(el => el.style.display = 'inline-block')
                    Vue.set(this.toggle, index, true)
                } else {
                    document.querySelectorAll(`[data-row-id="${index}"][data-hidable=true]`).forEach(el => el.style.display = 'none')
                    Vue.set(this.toggle, index, false)
                }
            },
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
                        let headers = response.data.headers
                        // rename Os to "Os family"
                        var index = _.findIndex(headers, {text: 'Os'})
                        let newOs = this._.clone(headers[index])
                        if (newOs) {
                            newOs.text = 'Os family'
                            headers.splice(index, 1, newOs)
                        }
                        this.mappingHeaders = headers
                        this.mappingItems = response.data.items
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during FeatureMappings data loading', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
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
                    this.editedMapItem = Object.assign({}, this.defaultMapItem)
                    this.editedIndex = -1
                })
            },
            // get columns width according to model
            paramMappingCols(model) {
                if (model == 'name')
                    return 12
                return 3
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
                    if (typeof(v) === 'object') {
                        item[k] = v !== null ? v.id : null
                    } else if (v === undefined || v === '') {
                        item[k] = null
                    } else {
                        item[k] = v
                    }
                }
                // back: edit existing one
                const url = `api/feature_mapping/${this.editedMapItem.id}/`
                let itemId = this.editedMapItem.id
                server
                    .patch(url, item)
                    .then(response => {
                        Object.assign(this.mappingItems[this.editedIndex], response.data)
                        this.$toasted.success('Successfully updated')
                        justEditedAnimation(itemId, 'selected-row-ok', 'data-row-map-id')
                        this.closeMapDialog()
                    })
                    .catch(error => {
                        if (error.response && error.response.status == 400) {
                            this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                        } else {
                            if (error.handleGlobally) {
                                error.handleGlobally('Could not update mapping', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        }
                        justEditedAnimation(itemId, 'selected-row-error', 'data-row-map-id')
                    })
            },
            deleteMappingItemDebounced(item) {
                // debounce needed to ensure that data loads first, while id exists in database
                this._.debounce(this.deleteMappingItem, 100)(item)
            },
            deleteMappingItem(item) {
                this.isMapDeleting = true
                const index = this.mappingItems.indexOf(item)
                let proceed = confirm('Are you sure you want to delete this item?')
                if (proceed) {
                    const url = `api/feature_mapping/${item.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            this.mappingItems.splice(index, 1)
                            this.$toasted.success('Successfully deleted')
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Could not delete mapping item', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                        .finally(() => this.showRulesTable = false)
                }
                this.isMapDeleting = false
            },
            exportMapping2Excel(item) {
                const url = `api/feature_mapping/export/${item.id}/`

                this.$store
                    .dispatch('reports/reportExcel', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Could not export mapping', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                        justEditedAnimation(itemId, 'selected-row-error', 'data-row-map-id')
                    })
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
                        if (this.headers[5])    // ids column
                            this.headers[5].width = 600
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Could not load feature mapping rules', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.loading = false)
            },
            // show dialog and prepare for editing
            editRuleItem(item) {
                this.editedIndex = this.items.indexOf(item)
                this.editedItem = Object.assign({}, item)
                this.editRuleItemDialog = true
                this.idItems = this.ids(this.editedItem.ids)
            },
            // Delete item from front and back
            deleteRuleItem(item) {
                this.loading = true
                const index = this.items.indexOf(item)
                let proceed = confirm('Are you sure you want to delete this item?')
                if (proceed) {
                    // send delete request to backend
                    const url = `api/feature_mapping/rules/${item.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            // remove from table
                            this.items.splice(index, 1)
                            this.$toasted.success('Successfully deleted')
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Could not delete item', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                }
                this.loading = false
            },
            // Create of save edited Rule
            saveRule() {
                // prepare item object to create/edit
                let item = {}
                for (let [k, v] of Object.entries(this.editedItem)) {
                    if (typeof(v) === 'object') {
                        item[k] = v !== null ? v.id : null
                    } else if (v === undefined || v === '') {
                        item[k] = null
                    } else {
                        item[k] = v
                    }
                }
                item.ids = this._.join(this.idItems, ',')
                if (item.ids == '')
                    item.ids = null

                // back: create new item back request ..
                if (this.editedIndex == -1) {
                    item.mapping = this.activeMapping.id
                    const url = 'api/feature_mapping/rules/'
                    server
                        .post(url, item)
                        .then(response => {
                            this.items.push(response.data)
                            this.$toasted.success('Successfully created')
                            this.closeRuleDialog()
                        })
                        .catch(error => {
                            if (error.response && error.response.status == 400) {
                                this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                            } else {
                                if (error.handleGlobally) {
                                    error.handleGlobally('Could not create rule', url)
                                } else {
                                    this.$toasted.global.alert_error(error)
                                }
                            }
                        })
                } else {
                    // .. edit existing one
                    const url = `api/feature_mapping/rules/${this.editedItem.id}/`
                    let itemId = this.editedItem.id
                    server
                        .patch(url, item)
                        .then(response => {
                            Object.assign(this.items[this.editedIndex], response.data)
                            this.$toasted.success('Successfully updated')
                            justEditedAnimation(itemId, 'selected-row-ok', 'data-row-rule-id')
                            this.closeRuleDialog()
                        })
                        .catch(error => {
                            if (error.response && error.response.status == 400) {
                                this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                            } else {
                                if (error.handleGlobally) {
                                    error.handleGlobally('Could not update rule', url)
                                } else {
                                    this.$toasted.global.alert_error(error)
                                }
                            }
                            justEditedAnimation(itemId, 'selected-row-error', 'data-row-rule-id')
                        })
                }
            },
            // Flush edit item object and close dialog
            closeRuleDialog() {
                this.editRuleItemDialog = false
                this.$nextTick(() => {
                    this.editedItem = Object.assign({}, this.defaultItem)
                    this.editedIndex = -1
                    this.idItems = []
                })
            },
            // get columns width according to model
            paramCols(model) {
                if (this._.includes(['scenario', 'ids'], model)) {
                    return 12
                } else if (model == 'feature') {
                    return 8
                } else {
                    return 4
                }
            }
        },
        created() {
            this.getMappings()

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
    .row-pointer >>> tbody tr :hover {
        cursor: pointer;
    }
    kbd {
        background-color: #546E7A;
    }
</style>