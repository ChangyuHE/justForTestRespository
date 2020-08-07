<template>
    <v-row justify="center">
        <!-- Groups/entities lists -->
        <v-col cols="2">
            <v-list
                expand class="pa-4" elevation="3"
                v-resize="onResize" :height="maxHeight" style="overflow-y: auto"
            >
                <v-list-group
                    v-for="group in groups" :key="group.name"
                    dense
                    v-model="openedGroups[group.name]"
                >
                    <!-- Title -->
                    <template v-slot:activator>
                        <v-list-item-content>
                            <v-list-item-title v-text="group.label" class="teal--text text--darken-4 font-weight-medium"></v-list-item-title>
                        </v-list-item-content>
                    </template>
                    <template v-for="(item, index) in group.items">
                        <v-list-item
                            v-if="item.name != 'divider'"
                            :key="item.name"
                            v-ripple="{ class: `primary--text` }"
                            @click=""
                        >
                            <!-- Content -->
                            <v-list-item-content @click="setActiveItem(item)">
                                {{ item.label }}
                            </v-list-item-content>

                            <!-- Request creation button -->
                            <v-list-item-action color="primary">
                                <v-hover v-slot:default="{ hover }">
                                    <v-icon v-show="item.requested"
                                        size="1.25em"
                                        :title="`Request new ${item.label} creation`"
                                        :class="{ 'primary--text': hover }"
                                        @click="setActiveItem(item); openRequestDialog()"
                                    >mdi-message-plus-outline</v-icon>
                                </v-hover>
                            </v-list-item-action>
                        </v-list-item>
                        <v-divider v-else :key="index"></v-divider>
                    </template>
                </v-list-group>
            </v-list>
        </v-col>

        <!-- Items data -->
        <v-col cols="6">
            <v-card v-if="active.name"
                class="pa-4" elevation="3"
                v-resize="onResize" :height="maxHeight" style="overflow-y: auto"
            >
                <v-data-table
                        dense multi-sort calculate-widths
                        :loading="loading"
                        :search="search"
                        :headers="computedTableHeaders"
                        :items="tableItems"
                        :items-per-page="30"
                        :footer-props="{'items-per-page-options':[15, 30, 50, 100, -1]}"
                    >
                        <template v-slot:top>
                            <v-toolbar flat>
                                <v-toolbar-title class="font-weight-medium">
                                    {{ active.label }}
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
                                <v-dialog v-model="editItemDialog" max-width="1000px">
                                    <!-- Add button -->
                                    <template v-slot:activator="{ on, attrs }">
                                        <v-btn v-show="canBeCreated"
                                            color="teal" dark fab small title="New item"
                                            class="mb-2 ml-2"
                                            v-bind="attrs"
                                            v-on="on"
                                        ><v-icon>mdi-plus</v-icon></v-btn>
                                    </template>
                                    <v-card>
                                        <v-card-title>
                                            <span class="headline">{{ active.label }} creation form</span>
                                        </v-card-title>
                                        <v-card-text>
                                            <v-divider></v-divider>
                                            <v-form v-model="isFormValid" @submit.prevent>
                                            <v-container>
                                                <v-row>
                                                    <!-- Params selectors -->
                                                    <template>
                                                        <v-col cols="12" class="pt-0 pb-1" v-for="field in fields[active.name]" :key="active.name + field.label">
                                                            <v-text-field v-if="field.type == 'text'"
                                                                color="blue-grey" clearable
                                                                :label="field.label"
                                                                v-model="editedItem[field.name]"
                                                                :rules="[rules.required(editedItem[field.name], field.name)]"
                                                            ></v-text-field>
                                                        </v-col>
                                                    </template>
                                                </v-row>
                                            </v-container>
                                            </v-form>
                                        </v-card-text>

                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="blue-grey darken-1" text @click="closeDialog">Cancel</v-btn>
                                            <v-btn color="cyan darken-2" text @click="save" :disabled="!isFormValid || saveDisabled">Save</v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-toolbar>
                        </template>
                        <!-- Actions icons -->
                        <template v-slot:item.actions="{ item }">
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Edit item"
                                    class="mr-1"
                                    :class="{ 'primary--text': hover }"
                                    @click="editItem(item)"
                                >
                                    mdi-pencil
                                </v-icon>
                            </v-hover>
                            <v-hover v-slot:default="{ hover }">
                                <v-icon
                                    small title="Delete item"
                                    :class="{ 'primary--text': hover }"
                                    @click="deleteItem(item)"
                                >
                                    mdi-delete
                                </v-icon>
                            </v-hover>
                        </template>
                    </v-data-table>
            </v-card>
        </v-col>
        <!-- Import errors dialog -->
        <v-dialog v-model="errorsDialog" max-width="50%">
            <v-card>
                <v-card-title class="gradient-warning-bottom">
                    <span class="headline">Something went wrong</span>
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

        <!-- Request Item dialog -->
        <v-dialog v-model="requestItemDialog" max-width="50%">
            <v-card>
                <v-card-title>
                    New {{ model }} item creation request
                </v-card-title>
                <v-card-text class="text-body-1">
                    <div> You are going to send request to administrators for {{ model }} item creation: </div>
                    <v-form v-model="isFormValid" @submit.prevent>
                        <v-col cols="12" class="pt-0 pb-1" v-for="field in fields[model]" :key="model + field.label">
                            <v-text-field v-if="field.type == 'text'"
                                color="blue-grey" clearable
                                :label="field.label"
                                :rules="[rules.required(requestedItem[field.name], field.name)]"
                                v-model="requestedItem[field.name]"
                            ></v-text-field>
                            <api-auto-complete v-else-if="field.type == 'autocomplete'"
                                class="my-0 pb-1"
                                type="defined"
                                color="blue-grey"
                                :model-name="field.name"
                                :rules="[rules.required(requestedItem[field.name], field.name)]"
                                v-model="requestedItem[field.name]"
                            ></api-auto-complete>
                        </v-col>
                    </v-form>

                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="blue-grey darken-1" text @click="closeRequestDialog" :disabled="sending">
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text @click="sendRequest" :loading="sending" :disabled="!isFormValid">
                        Send
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-row>
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
                groups: [
                    {
                        name: 'general', label: 'General',
                        items: [
                            { name: 'component', label: 'Component', requested: true }, { name: 'divider' },
                            { name: 'generation', label: 'Generation', requested: true }, { name: 'divider' },
                            { name: 'platform', label: 'Platform', requested: true }, { name: 'divider' },
                            { name: 'os', label: 'Os', requested: true }, { name: 'divider' },
                        ]
                    },
                    {
                        name: 'fmt', label: 'Feature Mapping', route: 'feature-mapping',
                        items: [
                            { name: 'milestone', label: 'Milestone', requested: true }, { name: 'divider' },
                            { name: 'feature', label: 'Feature', requested: false }, { name: 'divider' },
                            { name: 'scenario', label: 'Scenario', requested: false }, { name: 'divider' },
                        ]
                    }
                ],
                rules: {
                    required: (value, field) => {
                        if (this._.includes(['name', 'short_name', 'generation'], field))
                            return !!value || 'Required'
                        return true
                    }
                },
                fields: {
                    component: [
                        { label: 'Name', name: 'name', type: 'text' }
                    ],
                    generation: [
                        { label: 'Name', name: 'name', type: 'text' }
                    ],
                    platform: [
                        { label: 'Short name', name: 'short_name', type: 'text' },
                        { label: 'Name', name: 'name', type: 'text' },
                        { label: 'Aliases (optional)', name: 'aliases', type: 'text' },
                        { label: 'Generation', name: 'generation', type: 'autocomplete' }
                    ],
                    os: [
                        { label: 'Name', name: 'name', type: 'text' },
                        { label: 'Aliases (optional)', name: 'aliases', type: 'text' },
                    ],
                    milestone: [
                        { label: 'Name', name: 'name', type: 'text' }
                    ],
                    feature: [
                        { label: 'Name', name: 'name', type: 'text' }
                    ],
                    scenario: [
                        { label: 'Name', name: 'name', type: 'text' }
                    ]
                },
                active: {},
                items: [],
                openedGroups: {general: true, fmt: true},

                tableItems: [],
                tableHeaders: [],
                search: null,
                loading: false,

                isFormValid: null,
                editItemDialog: false,
                editedIndex: -1,
                editedItem: {},

                eData: {},
                errorsDialog: false,

                requestItemDialog: false,
                requestedItem: {},
                sending: false,

                maxHeight: 0,
            }
        },
        computed: {
            ...mapState(['userData']),
            computedTableHeaders() {
                // show all columns excepth of id one
                return this.tableHeaders.filter(h => h.value != 'id')
            },
            canBeCreated() {
                return !this.active.requested
            },
            model() {
                return this.active.name
            },
            saveDisabled() {
                return this._.isEqual(this.tableItems[this.editedIndex], this.editedItem)
            }
        },
        methods: {
            // setActiveItem(item, group) {
            setActiveItem(item) {
                this.active = item
                this.showItemValues()
            },
            // render data-table with active item data
            showItemValues() {
                this.tableItems = []
                this.tableHeaders = []
                this.loading = true

                let url = `api/${this._.lowerFirst(this.model)}/table/`

                server
                    .get(url)
                    .then(response => {
                        this.tableItems = response.data.items
                        this.tableHeaders = response.data.headers
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally && error.handleGlobally(`Error during ${name} data loading`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.loading = false)
            },
            // Create or save edited item
            save() {
                let toCreate = true
                if (this._.has(this.editedItem, 'id'))
                    toCreate = false

                let url = `api/${this.model}/`

                // back: create new item back request ..
                if (toCreate) {
                    server
                        .post(url, this.editedItem)
                        .then(response => {
                            this.$toasted.success(`Created new ${this.model} item`)

                            // update DataTable items (front)
                            if (this.editedIndex > -1) {
                                Object.assign(this.tableItems[this.editedIndex], this.editedItem)
                            } else {
                                this.tableItems.push(this.editedItem)
                            }
                        })
                        .catch(error => {
                            if (error.response && error.response.status == 400) {
                                let data = error.response.data
                                this.errorsDialog = true
                                this._.each(data, (message, title) => {
                                    this.eData[title] = message
                                })
                            } else {
                                if (error.handleGlobally) {
                                    error.handleGlobally && error.handleGlobally(`Error during ${this.model} item creation`, url)
                                } else {
                                    this.$toasted.global.alert_error(error)
                                }
                            }
                        })
                        .finally(() => {
                            this.closeDialog()
                            this.showItemValues()
                        })
                } else {
                    // .. edit existing one
                    const url = `api/${this.model}/${this.editedItem.id}/`
                    server
                        .patch(url, this.editedItem)
                        .then(response => {
                            console.log(response)
                            this.$toasted.success('Successfully updated')

                            // update DataTable items (front)
                            if (this.editedIndex > -1) {
                                Object.assign(this.tableItems[this.editedIndex], this.editedItem)
                            } else {
                                this.tableItems.push(this.editedItem)
                            }
                        })
                        .catch(error => {
                            if (error.response && error.response.status == 400) {
                                let data = error.response.data
                                this.errorsDialog = true
                                this._.each(data, (message, title) => {
                                    this.eData[title] = message
                                })
                            } else {
                                if (error.handleGlobally) {
                                    error.handleGlobally && error.handleGlobally(`Error during ${this.model} item creation`, url)
                                } else {
                                    this.$toasted.global.alert_error(error)
                                }
                            }
                        })
                        .finally(() => this.closeDialog())
                }
            },
            // Delete item from front and back
            deleteItem(item) {
                this.loading = true
                const index = this.tableItems.indexOf(item)
                let proceed = confirm('Are you sure you want to delete this item?')
                if (proceed) {
                    // send delete request to backend
                    const url = `api/${this.model}/${item.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            // remove from table
                            this.tableItems.splice(index, 1)
                            this.$toasted.success('Successfully deleted')
                        })
                        .catch(error => {
                            error.handleGlobally && error.handleGlobally('Could not delete item', url)
                        })
                    }
                this.loading = false
            },
            // Show dialog and prepare for editing
            editItem(item) {
                this.editedIndex = this.tableItems.indexOf(item)
                this.editedItem = Object.assign({}, item)
                this.editItemDialog = true
            },
            // Flush edit item object and close dialog
            closeDialog() {
                this.editItemDialog = false
                this.$nextTick(() => {
                    this.editedItem = {}
                    this.editedIndex = -1
                })
            },
            openRequestDialog() {
                this.requestItemDialog = true
            },
            closeRequestDialog() {
                this.requestItemDialog = false
                this.$nextTick(() => {
                    this.requestedItem = {}
                })
            },
            // Send item creation request
            sendRequest() {
                this.sending = true
                let data = { model: this.model, fields: {}, requester: this.userData }
                // prepare item data to send
                for (let [k, v] of Object.entries(this.requestedItem)) {
                    // change auto-complete fields
                    if (typeof(v) === 'object') {
                        this.requestedItem[k] = v !== null ? v.name : null
                        data.fields[k] = v !== null ? v.id : null
                    // empty fields
                    } else if (v === undefined || v === '') {
                        this.requestedItem[k] = null
                        data.fields[k] = null
                    // text and boolean values
                    } else {
                        data.fields[k] = v
                    }
                }
                server
                    .post('api/objects/create/', data)
                    .then(response => {
                        this.requestItemDialog = false
                        this.$toasted.success('Request has been sent')
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during requesting creation of a new object', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => {
                        this.sending = false
                        this.closeRequestDialog()
                    })
            },
            // set max height variable according to browser's inner size
            onResize () {
                this.maxHeight = window.innerHeight - 100
            },
        },
        mounted () {
            this.onResize()
        }
    }
</script>