<template>
    <v-dialog
        v-model="dialog"
        max-width="50%"
    >
        <v-overlay :value="pageReload">
            <v-progress-circular indeterminate size="64"></v-progress-circular>
        </v-overlay>
        <v-card>
            <v-card-title>
                User Profiles
            </v-card-title>
            <v-card-text >
                <v-col class="d-flex flex-row">
                    <!-- Profiles tabs -->
                    <v-tabs
                        style="max-width: 90%"
                        show-arrows
                        v-model="tab"
                        @change="getFiltersTableData"
                    >
                        <v-tab
                            v-for="profile in profiles"
                            :key="profile.id"
                        >
                            <v-badge
                                v-if="profile.active"
                                color="primary"
                                class="active-badge"
                                content="Default"
                            >
                                {{ profile.name }}
                            </v-badge>
                            <span v-else>{{ profile.name }}</span>
                        </v-tab>
                    </v-tabs>
                    <v-spacer></v-spacer>

                    <!-- Actions -->
                    <div class="d-flex align-center">
                        <!-- Edit profile icon / inline dialog -->
                        <v-dialog
                            max-width="30%"
                            v-model="editDialog"
                        >
                            <template v-slot:activator="{ on }">
                                <v-hover v-slot:default="{ hover }">
                                    <v-icon
                                        v-on="on"
                                        small title="Edit name"
                                        class="mr-1"
                                        :class="{ 'primary--text': hover }"
                                    >
                                        mdi-pencil
                                    </v-icon>
                                </v-hover>
                            </template>
                            <v-card>
                                <v-card-title>Edit profile</v-card-title>
                                    <v-card-text>
                                        <v-form v-model="isFormValid" @submit.prevent>
                                            <v-text-field
                                                label="New name"
                                                :rules="[rules.required(editedName), rules.isLongEnough(editedName, 3), noDuplicates(editedName)]"
                                                v-model.trim="editedName"
                                                :placeholder="profiles[tab].name"
                                            ></v-text-field>
                                        </v-form>
                                    </v-card-text>
                                <v-card-actions class="pt-0">
                                    <v-spacer></v-spacer>
                                    <v-btn
                                        text
                                        color="blue-grey darken-1"
                                        @click="editDialog = false"
                                    >
                                        Close
                                    </v-btn>
                                    <v-btn
                                        text
                                        color="primary"
                                        :disabled="!isFormValid || editing"
                                        @click="editProfile('name')"
                                    >
                                        Save
                                    </v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-dialog>

                        <!-- Clean profile icon -->
                        <v-hover v-slot:default="{ hover }">
                            <v-icon
                                small title="Clean profile"
                                class="mr-1"
                                :class="{ 'primary--text': hover }"
                                @click="editProfile('clean')"
                            >
                                mdi-broom
                            </v-icon>
                        </v-hover>

                        <!-- Delete profile icon -->
                        <v-hover v-slot:default="{ hover }">
                            <v-icon
                                small title="Delete profile"
                                class="mr-1"
                                :class="{ 'primary--text': hover }"
                                :disabled="isActiveProfile"
                                @click="deleteProfile"
                            >
                                mdi-delete
                            </v-icon>
                        </v-hover>
                    </div>
                </v-col>

                <!-- Profile data tables -->
                <v-tabs-items v-model="tab">
                    <v-tab-item
                        v-for="profile in profiles"
                        :key="profile.id"
                    >
                        <v-data-table
                            class="px-2 pt-4"
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
                                    <td>{{ item.value }}</td>
                                </tr>
                            </template>
                        </v-data-table>
                    </v-tab-item>
                </v-tabs-items>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    text
                    color="blue-grey darken-2"
                    @click="dialog = false"
                >
                    Close
                </v-btn>
                <v-btn
                    text
                    color="primary"
                    :disabled="deleting || isActiveProfile"
                    :loading="activating"
                    @click="activateProfile"
                >
                    Activate
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
    import { mapState } from 'vuex'
    import qs from 'query-string'
    import server from '@/server.js'
    import rules from '@/utils/form-rules.js'
    import { isIDsFilter } from '@/components/tree/common.js'

    export default {
        data() {
            return {
                tab: 0,
                dialog: true,
                filtersSaveHeaders: [
                    { text: 'Category', value: 'category' },
                    { text: 'Filter', value: 'name', groupable: false },
                    { text: 'Value', value: 'value', groupable: false },
                ],
                rules: rules,
                filtersSaveItems: [],

                activating: false,
                pageReload: false,
                editedName: '',
                editDialog: false,
                isFormValid: false,
                editing: false,
                deleting: false,
            }
        },
        watch: {
            dialog(value) {
                value || this.$emit('close')
            },
            editDialog(value) {
                value || this.closeEditDialog()
            }
        },
        computed: {
            ...mapState(['userData']),
            profiles() {
                return this._.orderBy(this.userData.profiles, ['active', 'id'], ['desc', 'asc'])
            },
            isActiveProfile() {
                return this.profiles[this.tab].active
            },
            noDuplicates() {
                return value => {
                    return !this._.map(this.userData.profiles, 'name').includes(value) || 'Already exists'
                }
            }
        },
        methods: {
            getFiltersTableData() {
                if (this.tab === undefined) {
                    return
                }
                let profile = this.profiles[this.tab]
                this.filtersSaveItems = []
                const getCategory = type => {
                    if (type === 'treeFilter') {
                        return 'Tree Filter'
                    } else if (type === 'treeDates') {
                        return 'Tree Dates'
                    }
                    return undefined
                }
                this._.keys(profile.data).forEach(key => {
                    let value = profile.data[key].formatted
                    let [category, name] = key.split('-')
                    this.filtersSaveItems.push({'name': name, 'value': value, 'category': getCategory(category)})
                })
            },
            activateProfile() {
                this.activating = true

                // set selected profile as active
                let profile = this._.cloneDeep(this.profiles[this.tab])
                profile.active = true
                profile.to_activate = true

                const url = `api/users/current/profile/${profile.id}`
                server
                    .patch(url, profile)
                    .then(_ => {
                        this.pageReload = true

                        let params = {}
                        // get raw values from profile data
                        this._.each(this.profiles[this.tab].data, (obj, key) => {
                            let name = key.split('-')[1]
                            if (isIDsFilter(name)) {
                                params[key] = this._.map(obj.value, 'id')
                            } else {
                                params[key] = obj.value
                            }
                        })
                        // apply them to URL and go to new page
                        window.location = `${qs.parseUrl(location.href).url}?${qs.stringify(params, {arrayFormat: 'comma'})}`
                    })
                    .catch(error => {
                        if (error.response && error.response.status === 400) {
                            this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                        } else {
                            if (error.handleGlobally) {
                                error.handleGlobally('Error in user profile active status update', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        }
                    })
                    .finally(() => this.activating = false )
            },
            editProfile(type) {
                this.editing = true
                let profile = this._.cloneDeep(this.profiles[this.tab])
                if (type === 'clean') {
                    profile.data = null
                } else {
                    profile.name = this.editedName
                }
                const url = `api/users/current/profile/${profile.id}`
                server
                    .patch(url, profile)
                    .then(response => {
                        this.$toasted.success('Profile was updated')
                        this.$store.dispatch('setUserDataManually', response.data).then(() => {
                            this.$nextTick(() => {
                                this.getFiltersTableData()
                            })
                        })
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error in user profile update', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.closeEditDialog())
            },
            closeEditDialog() {
                this.editDialog = false
                this.editing = false
                this.$nextTick(() => {
                    this.editedName = ''
                })
            },
            deleteProfile() {
                this.deleting = true
                const url = `api/users/current/profile/${this.profiles[this.tab].id}`
                server
                    .delete(url)
                    .then(response => {
                        this.$store.dispatch('setUserDataManually', response.data)
                        this.tab = 0
                        this.getFiltersTableData()
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error in user profile delete', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.deleting = false)
            }
        },
        mounted() {
            this.getFiltersTableData()
        }
    }
</script>

<style>
    .active-badge .v-badge__badge {
        font-size: 0.65em;
        padding-top: 2px;
        padding-left: 4px;
        padding-right: 4px;
        height: 14px;
        left: calc(80%) !important;
        top: -14px !important;
    }
</style>
