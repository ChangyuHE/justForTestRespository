<template>
    <v-dialog
        v-if="validation"
        v-model="dialog"
        max-width="45%"
        scrollable
    >
        <v-card>
            <v-card-title>{{ cardTitle }}</v-card-title>
            <v-card-text>
                <span class="text-subtitle-2 px-2">{{ branch }}</span>
                <v-form v-model="isFormValid">
                    <v-col>
                        <v-simple-table>
                            <template v-slot:default>
                                <tr
                                    v-for="(field, i) in fields"
                                    :key="i"
                                >
                                    <td style="width: 15%">
                                        <span
                                            v-if="field !== 'divider'"
                                            class="text-subtitle-1 font-size-medium row-title"
                                        >
                                            {{ field }}
                                        </span>
                                        <v-divider v-else></v-divider>
                                    </td>
                                    <td class="py-2 px-1">
                                        <v-col
                                            v-if="field !== 'divider'"
                                            :cols="fieldsToCols(field)"
                                            class="py-0 px-0"
                                        >
                                            <!-- Name -->
                                            <v-text-field
                                                v-if="field == 'name'"
                                                :color="getChangeColor('name')"
                                                class="py-0"
                                                :clearable="isOwner"
                                                :readonly="!isOwner"
                                                :rules="isOwner ? [rules.isLongEnough(validation.name, 10), noDuplicates(validation.name)] : []"
                                                v-model="validation.name"
                                            >
                                                <template v-slot:append-outer>
                                                    <v-icon
                                                        v-if="isChanged('name')"
                                                        color="primary"
                                                        small
                                                    >
                                                        mdi-asterisk
                                                    </v-icon>
                                                </template>
                                            </v-text-field>

                                            <!-- Date -->
                                            <v-menu
                                                v-if="field == 'date'"
                                                class="mr-2"
                                                nudge-right="150"
                                                min-width="290px"
                                                transition="scale-transition"
                                                :close-on-content-click="false"
                                                :disabled="!isOwner"
                                                v-model="menu"
                                            >
                                                <template v-slot:activator="{ on }">
                                                    <v-text-field
                                                        prepend-inner-icon="mdi-calendar"
                                                        :color="getChangeColor('date')"
                                                        class="py-0"
                                                        hide-details
                                                        :readonly="!isOwner"
                                                        v-on="on"
                                                        v-model="validation.date"
                                                    >
                                                        <template v-slot:append-outer>
                                                            <v-icon
                                                                v-if="isChanged('date')"
                                                                color="primary"
                                                                small
                                                            >
                                                                mdi-asterisk
                                                            </v-icon>
                                                        </template>
                                                    </v-text-field>
                                                </template>
                                                <v-date-picker
                                                    header-color="blue-grey"
                                                    color="blue-grey darken-2"
                                                    :max="today"
                                                    v-model="validation.date"
                                                    @input="menu = false"
                                                ></v-date-picker>
                                            </v-menu>

                                            <!-- Owner -->
                                            <div v-if="field == 'owner'"
                                                class="text-subtitle-2 d-flex-inline align-self-center"
                                            >
                                                <span v-html="ownerData"></span>
                                                <!-- Mail To icon -->
                                                <v-hover v-slot:default="{ hover }">
                                                    <a :href="'mailto:' + validation.owner.email" :title="'Mail to ' + validation.owner.first_name" style="text-decoration: none">
                                                        <v-icon class="pl-1 align-start" :class="{ 'primary--text': hover }">
                                                            mdi-email-edit-outline
                                                        </v-icon>
                                                    </a>
                                                </v-hover>
                                            </div>

                                            <!-- Gen -->
                                            <span
                                                v-if="field == 'gen'"
                                                class="text-subtitle-2"
                                            >
                                                {{ validation.platform.generation.name }}
                                            </span>

                                            <!-- Platform -->
                                            <span v-if="field == 'platform'">
                                                Short Name: <span class="text-subtitle-2">{{ validation.platform.short_name }}</span><br>
                                                Full Name: <span class="text-subtitle-2">{{ validation.platform.name }}</span><br>
                                                Aliases: <span class="text-subtitle-2">{{ aliases(validation.platform) }}</span>
                                            </span>

                                            <!-- Os and Family -->
                                            <span v-if="field == 'os'">
                                                Name: <span class="text-subtitle-2">{{ validation.os.name }}</span><br>
                                                Aliases: <span class="text-subtitle-2">{{ aliases(validation.os) }}</span>
                                            </span>
                                            <span
                                                v-if="field == 'family'"
                                                class="text-subtitle-2"
                                            >
                                                {{ validation.os.parent_os.name }}
                                            </span>

                                            <!-- Env -->
                                            <span
                                                v-if="field == 'env'"
                                                class="text-subtitle-2"
                                            >
                                                {{ validation.env.name }}
                                            </span>

                                            <!-- Components and Features -->
                                            <template v-if="['components', 'features'].includes(field)">
                                                <v-chip-group v-if="validation[field].length">
                                                    <v-chip
                                                        v-for="item in validation[field]"
                                                        :key="item.name"
                                                        class="py-0 my-0"
                                                        small
                                                    >
                                                        {{ item.name }}
                                                    </v-chip>
                                                </v-chip-group>
                                                <span v-else class="text-subtitle-2">No</span>
                                            </template>

                                            <!-- Notes -->
                                            <v-textarea v-if="field == 'notes'"
                                                :color="getChangeColor('notes')"
                                                class="py-0 text-body-2"
                                                rows="1"
                                                auto-grow clearable hide-details
                                                :clearable="isOwner"
                                                :readonly="!isOwner"
                                                v-model="validation.notes"
                                            >
                                                <template v-slot:append-outer>
                                                    <v-icon
                                                        v-if="isChanged('notes')"
                                                        color="primary"
                                                        small
                                                    >
                                                        mdi-asterisk
                                                    </v-icon>
                                                </template>
                                            </v-textarea>
                                        </v-col>
                                        <v-divider v-else></v-divider>
                                    </td>
                                </tr>
                            </template>
                        </v-simple-table>
                    </v-col>
                </v-form>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    text
                    color="blue-grey darken-1"
                    @click="dialog = false"
                >
                    Close
                </v-btn>
                <v-btn
                    v-if="isOwner"
                    text
                    color="primary"
                    :disabled="!isFormValid || _.isEqual(originalValidation, validation)"
                    @click="save"
                >
                    Save
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
    import { mapState } from 'vuex'
    import server from '@/server.js'

    import { getBranchForLeaf } from './common.js'
    import rules from '@/utils/form-rules.js'

    export default {
        props: {
            node: { type: Object, required: true },
            treeStructure: { type: Array, required: true }
        },
        data() {
            return {
                dialog: true,
                validation: undefined,
                rules: rules,
                isFormValid: false,
                fields: [
                    'name', 'date', 'owner', 'divider',
                    'gen', 'os', 'family', 'platform', 'env', 'divider',
                    'components', 'features', 'divider',
                    'notes'
                ],
                canBeChanged: [
                    'name', 'date', 'notes'
                ],
                menu: null
            }
        },
        computed: {
            ...mapState(['userData']),
            isOwner() {
                return this.validation.owner.id == this.userData.id
            },
            noDuplicates() {
                return value => {
                    if (value != this.node.model.text_flat) {
                        return rules.uniqueNameInBranch(value, this.nodeNeighbours)
                    }
                    return true
                }
            },
            nodeNeighbours() {
                return this.node.$parent.$children.map(node => node.model.text_flat)
            },
            cardTitle() {
                return this.isOwner ? 'Edit validation properties' : 'Validation properties'
            },
            branch() {
                let nodes = this._.map(getBranchForLeaf(this.node), node => node.model.text_flat).reverse()
                return `${nodes[5]} (${nodes[1]}, ${nodes[3]}, ${nodes[4]})`
            },
            ownerData() {
                let owner = this.validation.owner
                return `${owner.fullname} (${owner.username})`
            },
            today() {
                let date = new Date()
                return date.toISOString()
            },
            aliases() {
                return obj => obj.aliases ? obj.aliases.split(';').filter(e => !!e).join(', ') : 'No'
            },
            fieldsToCols() {
                return name => {
                    if (name === 'date') {
                        return 2
                    } else {
                        return 12
                    }
                }
            },
            isChanged(field) {
                return field => !this._.isEqual(this.validation[field], this.originalValidation[field])
            },
            getChangeColor(field) {
                return field => this.isChanged(field) ? 'blue-grey' : 'primary'
            }
        },
        watch: {
            dialog() {
                this.$emit('close')
            }
        },
        methods: {
            save() {
                let data = {}
                this.canBeChanged.forEach(field => {
                    if (!this._.isEqual(this.validation[field], this.originalValidation[field])) {
                        data[field] = this.validation[field]
                    }
                })

                const url = `api/validations/update/${this.validation.id}/`
                server
                    .patch(url, data)
                    .then(response => {
                        this.$toasted.success('Validation data succesfully updated')
                        // reload page in case of validation "outer" data update
                        if ('name' in data) {
                            window.location.reload()
                        }
                    })
                    .catch(error => {
                        if (error.response && error.response.status === 400) {
                            this.$toasted.global.alert_error(JSON.stringify(error.response.data))
                        } else {
                            if (error.handleGlobally) {
                                error.handleGlobally(`Error during validation update`, url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        }
                    })
                    .finally(() => this.dialog = false)
            }
        },
        created() {
            const url = `api/validations/${this.node.model.id}/`
            server
                .get(url)
                .then(response => {
                    this.validation = this._.pickBy(response.data, (value, key) => this.fields.includes(key));
                    // find items from tree structure by ids
                    ['components', 'features'].map(key => {
                        const variants = this.treeStructure.find(selector => selector.level == key.slice(0, -1))
                        if (variants) {
                            this.validation[key] = variants.items.filter(item => this.validation[key].includes(item.id))
                        }
                    })
                    this.validation.id = response.data.id
                    this.originalValidation = this._.cloneDeep(this.validation)
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Could not get validation data', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
        }
    }
</script>

<style scoped>
    .row-title {
        text-transform: capitalize;
    }
</style>
