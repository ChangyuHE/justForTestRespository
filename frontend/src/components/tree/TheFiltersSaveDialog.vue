<template>
    <v-dialog
        v-model="dialog"
        max-width="40%"
    >
        <v-card>
            <v-card-title>
                Saving filters to profile
            </v-card-title>
            <v-card-text>
                <v-card-subtitle class="text-subtitle-1 pa-2">Select profile to update or create new one</v-card-subtitle>
                <v-col cols="5" class="py-0 d-flex">
                    <v-autocomplete
                        class="pb-4 pt-0"
                        color="blue-grey"
                        item-color="blue-grey"
                        clear-icon="mdi-close"
                        item-text="name"
                        item-value="id"
                        clearable hide-details return-object
                        :menu-props="{closeOnContentClick: true}"
                        :items="userData.profiles"
                        v-model="selectedProfile"
                        @change="fillDefaultsTableData"
                    ></v-autocomplete>

                    <!-- Inplace dialog for profile creation -->
                    <v-dialog
                        v-model="profileCreationDialog"
                        persistent no-click-animation
                        max-width="30%"
                    >
                        <template v-slot:activator="{ on }">
                            <v-btn v-on="on" icon>
                                <v-icon>mdi-plus</v-icon>
                            </v-btn>
                        </template>
                        <v-card>
                            <v-card-title>New profile creation</v-card-title>
                            <v-form v-model="isFormValid">
                                <v-card-text>
                                    <v-text-field
                                        color="blue-grey"
                                        class="py-0 my-0"
                                        label="Name"
                                        :rules="[rules.required(newProfile), rules.isLongEnough(newProfile, 3), noDuplicates(newProfile)]"
                                        v-model.trim="newProfile"
                                    ></v-text-field>
                                </v-card-text>
                            </v-form>
                            <v-card-actions class="pt-0">
                                <v-spacer></v-spacer>
                                <v-btn color="blue-grey darken-1" text @click="profileCreationDialog = false">
                                    Close
                                </v-btn>
                                <v-btn color="primary" text :disabled="!isFormValid" @click="createProfile">
                                    Create
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-col>

                <!-- DataTable with selected filters -->
                <v-data-table
                    class="px-2"
                    dense
                    group-by="category" show-group-by
                    :headers="filtersSaveHeaders"
                    :items="filtersSaveItems"
                >
                    <template v-slot:group="props">
                        <tr>
                            <td colspan=4>
                                <span class="ml-n2 font-weight-medium text-body-1 blue-grey--text text--darken-1">
                                    {{ props.group }}
                                </span>
                            </td>
                        </tr>
                        <tr v-for="item in props.items" :key="item.name" :class="item.statusClass">
                            <td><strong>{{ item.name }}</strong></td>
                            <td>{{ item.oldValue }}</td>
                            <td>{{ item.value }}</td>
                            <td>
                                <template v-if="props.group != 'To be removed'">
                                    <v-icon small @click="deleteFilterItem(item)">
                                        mdi-delete
                                    </v-icon>
                                </template>
                            </td>
                        </tr>
                    </template>
                </v-data-table>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue-grey darken-1" text @click="dialog = false">
                    Close
                </v-btn>
                <v-btn color="primary" text :disabled="!Object.keys(filtersSaveItems).length || !selectedProfile" @click="saveFilters">
                    Submit
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
    import { mapState, mapGetters } from 'vuex'
    import server from '@/server.js'

    import rules from '@/utils/form-rules.js'
    import { isIDsFilter, filterItemText } from './common.js'
    import { dateStart, dateEnd, sliderButtons } from './dates.js'

    const SETTINGS_STATUSES = {
        diff: 'settings-different',
        new: 'settings-new',
        delete: 'settings-delete'
    }

    export default {
        props: {
            selectors: {type: Object, required: true},
            dates: {type: Object, required: true}
        },
        data() {
            return {
                dialog: true,
                filtersSaveHeaders: [
                    { text: 'Category', value: 'category' },
                    { text: 'Filter', value: 'name', groupable: false },
                    { text: 'Old value', value: 'oldValue', groupable: false },
                    { text: 'New value', value: 'value', groupable: false },
                    { text: 'Actions', value: 'actions', sortable: false, groupable: false, width: 80 }
                ],
                filtersSaveItems: [],
                profileCreationDialog: false,
                newProfile: '',
                selectedProfile: undefined,
                rules: rules,
                isFormValid: false
            }
        },
        watch: {
            dialog(value) {
                value || this.$emit('close')
            },
            profileCreationDialog(value) {
                value || this.closeProfileCreateDialog()
            }
        },
        computed: {
            ...mapState(['userData']),
            ...mapGetters(['activeProfile']),
            noDuplicates() {
                return value => {
                    return !this._.map(this.userData.profiles, 'name').includes(value) || 'Already exists'
                }
            }
        },
        methods: {
            fillDefaultsTableData() {
                this.filtersSaveItems = []
                if (this._.isEmpty(this.selectedProfile)) {
                    return
                }
                const getStatus = (isNew, isDifferent) => {
                    if (isNew) {
                        return SETTINGS_STATUSES['new']
                    } else if(isDifferent) {
                        return SETTINGS_STATUSES['diff']
                    }
                    return undefined
                }
                const getFilterValues = (category, keyPrefix, key, value) => {
                    let originalKey = `${keyPrefix}-${key}`     // example: treeFilter-platform
                    let oldValue = this.getFromProfile(originalKey)
                    return {
                        'category': category,
                        'name': key, 'value': this.composeOutputValue(key, value),
                        'original_key': originalKey, 'original_value': value, 'oldValue': this.composeOutputValue(key, oldValue),
                        'statusClass': getStatus(!oldValue && (value !== oldValue), !this.isEqualValues(key, value, oldValue))
                    }
                }
                // Tree filters
                this._.each(this.selectors, (value, key) => {
                    if (!_.isEmpty(value)) {
                        this.filtersSaveItems.push(getFilterValues('Tree Filter', 'treeFilter', key, value))
                    }
                })
                // Date filters
                if (this.dates.enabled) {
                    this._.each({'range': this.dates.sliderRange, 'button': this.dates.sliderButton}, (value, key) => {
                        if (value !== null && value !== undefined) {
                            this.filtersSaveItems.push(getFilterValues('Tree Dates', 'treeDates', key, value))
                        }
                    })
                }
                // from profile
                let keysInProfileOnly = this._.difference(this._.keys(this.selectedProfile.data), this._.map(this.filtersSaveItems, 'original_key'))
                keysInProfileOnly.forEach(key => {
                    let value = this.selectedProfile.data[key].value
                    this.filtersSaveItems.push({
                        'category': 'To be removed',
                        'name': key, 'value': '',
                        'original_key': undefined, 'original_value': undefined, 'oldValue': this.composeOutputValue(key.split('-')[1], value),
                        'statusClass': SETTINGS_STATUSES['delete']
                    })
                })
            },
            composeOutputValue(name, value) {
                // Dates
                if (name === 'range' && !this._.isEmpty(value)) {
                    return `${dateStart(value[0])} \u2013 ${dateEnd(value[1])}`
                } else if (name == 'button' && value) {
                    return sliderButtons[value]['text']
                }
                // Tree Filters
                if (isIDsFilter(name)) {
                    return this._.map(value, filterItemText(name)).join(', ')
                } else {
                    return value
                }
            },
            isEqualValues(key, a, b) {
                if (typeof a === typeof b) {
                    if (this._.isArray(a) && isIDsFilter(key)) {
                        a = this._.sortBy(this._.map(a, 'id'))
                        b = this._.sortBy(this._.map(b, 'id'))
                    }
                    return this._.isEqual(a, b)
                }
                return false
            },
            getFromProfile(key) {
                if ((!this._.isEmpty(this.selectedProfile.data) && (key in this.selectedProfile.data))) {
                    return this.selectedProfile.data[key].value
                }
                return undefined
            },
            deleteFilterItem(item) {
                const index = this.filtersSaveItems.indexOf(item)
                this.filtersSaveItems.splice(index, 1)
            },
            saveFilters() {
                let filters = {}
                this.filtersSaveItems.forEach(item => {
                    if (item.category !== 'To be removed') {
                        filters[item.original_key] = {
                            // raw data, like indexes, ids and so on
                            value: item.original_value,
                            // pre-formatted values to show on page
                            formatted: item.value
                        }
                    }
                })
                let profile = this._.cloneDeep(this.selectedProfile)
                profile.data = filters

                const url = `api/users/current/profile/${profile.id}`
                server
                    .patch(url, profile)
                    .then(response => {
                        this.$toasted.success(`User profile ${profile.name} updated`)
                        this.$store.dispatch('setUserDataManually', response.data)
                    })
                    .catch(error => {
                        if (error.response && error.response.status === 400) {
                            this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                        } else {
                            if (error.handleGlobally) {
                                error.handleGlobally(`Error in user profile update`, url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        }
                    })
                    .finally(() => this.closeSaveFilters())
            },
            closeSaveFilters() {
                this.dialog = false
                this.$nextTick(() => {
                    this.filtersSaveItems = []
                })
            },
            createProfile() {
                const url = 'api/users/current/profile/'
                server
                    .post(url, {name: this.newProfile})
                    .then(response => {
                        this.$toasted.success(`New user profile "${this.newProfile}" created`)

                        // set value for dropdown
                        this.selectedProfile = response.data
                        // update user data
                        this.$store
                            .dispatch('getUserData')
                            .then(() => this.fillDefaultsTableData())
                    })
                    .catch(error => {
                        if (error.response && error.response.status === 400) {
                            this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                        } else {
                            if (error.handleGlobally) {
                                error.handleGlobally(`Error in user profile creation`, url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        }
                    })
                    .finally(() => this.closeProfileCreateDialog())
            },
            closeProfileCreateDialog() {
                this.profileCreationDialog = false
                this.$nextTick(() => {
                    this.newProfile = ''
                })
            },
        },
        mounted() {
            this.selectedProfile = this.activeProfile
            this.fillDefaultsTableData()
        }
    }
</script>

<style scoped>
    .settings-different {
        background-color: #ffaa001c;
    }
    .settings-delete {
        background-color: #f443361c;
    }
    .settings-new {
        background-color: #4caf501c;
    }
</style>
