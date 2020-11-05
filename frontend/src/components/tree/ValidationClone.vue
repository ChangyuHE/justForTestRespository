<template>
    <!-- Clone validation dialog -->
    <v-form v-model="valid">
        <v-dialog
            v-if="showCloneDialog"
            v-model="showCloneDialog"
            no-click-animation
            max-width="40%"
        >
            <v-card>
                <v-card-title>Validation clone</v-card-title>
                <v-card-subtitle class="my-0 py-0">{{ selectedNode.model.name }}</v-card-subtitle>
                    <v-col cols="12" class="px-6">
                        <v-text-field
                            color="blue-grey"
                            label="Name for validation clone"
                            :rules="[rules.isLongEnough(validationClone.name),
                                     rules.uniqueName(validationClone.name, nodeNeighbours)]"
                            v-model="validationClone.name"
                        ></v-text-field>
                    </v-col>
                    <v-col cols="12" class="px-6">
                        <v-text-field
                            color="blue-grey"
                            label="Notes to add to validation clone"
                            v-model="validationClone.notes"
                        ></v-text-field>
                    </v-col>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="cyan darken-2" text
                        :disabled="validationCloneLoading"
                        @click="closeCloneDialog"
                    >
                        Close
                    </v-btn>
                    <v-btn color="cyan darken-2" text
                        :disabled="!valid"
                        :loading="validationCloneLoading" @click="cloneValidation"
                    >
                        Clone
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-form>
</template>

<script>
    import { mapState } from 'vuex'
    import server from '@/server.js'

    export default {
        data() {
            return {
                valid: false,
                showCloneDialog: true,
                validationCloneLoading: false,
                validationClone: {name: '', notes: ''},
                rules: {
                    isLongEnough(value) {
                        return value.length < 10 ? 'At least 10 symbols' : true
                    },

                    // check if val with this name is not exists in one branch with selected validation
                    uniqueName(value, neighbours) {
                        return neighbours.includes(value) ? 'Duplicated name' : true
                    }
                },
            }
        },
        props: {
            selectedNode: { type: Object, required: true },
        },
        watch: {
            showCloneDialog(val) {
                this.closeCloneDialog()
            }
        },
        computed: {
            ...mapState('tree', ['validations']),
            // nodes in one branch with first selected node
            nodeNeighbours() {
                return this.selectedNode.$parent.$children.map(node => { return node.model.text })
            },
            // create unique name for validation clone
            cloneDefaultName() {
                let today = new Date()
                let date = today.getFullYear().toString().substr(-2) + '.' + (today.getMonth() + 1) + '.' + today.getDate()
                let time = today.getHours() + ':' + today.getMinutes()
                let dateTime = date + '_' + time

                return this.selectedNode.model.text + '_clone_' + dateTime
            },
        },
        methods: {
            closeCloneDialog() {
                this.showCloneDialog = false
                this.validationClone.name = ''
                this.validationClone.notes = ''
                this.$emit('close')
            },
            cloneValidation() {
                this.validationCloneLoading = true
                const url = 'api/import/clone/'
                server
                    .post(url, {validation_name: this.validationClone.name,
                                 notes: this.validationClone.notes,
                                 validation_id: this.validations[0]})
                    .then(response => {
                        this.$toasted.success('Cloning started in the background.<br>\n' +
                                              'You will be notified by email at the end.', { duration: 6000 })
                        this.closeCloneDialog()
                    })
                    .catch(error => {
                        if(error.response.status != 422) {
                            if (error.handleGlobally) {
                                error.handleGlobally('Failed to clone validation', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        } else {
                            let errors = error.response.data.errors.map(function(elem){ return elem.message }).join('<br>')
                            this.$toasted.global.alert_error(errors)
                        }
                    })
                    .finally(() => {
                        this.validationCloneLoading = false
                    })
            },
        },
        mounted() {
            this.validationClone.name = this.cloneDefaultName
        }
    }
</script>