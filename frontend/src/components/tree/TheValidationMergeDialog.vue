<template>
    <!-- Merge validation dialog -->
    <v-form v-model="valid">
        <v-dialog
            no-click-animation
            max-width="40%"
            v-if="showMergeDialog"
            v-model="showMergeDialog"
        >
            <v-card>
                <v-card-title class="pb-1">Validations merge</v-card-title>
                <v-card-subtitle class="mt-0 mb-2 py-0 text-subtitle-2">{{ branchInfo }}</v-card-subtitle>
                <v-card-subtitle v-for="node of selectedNodes" :key="node.model.name" class="my-0 py-0">{{ node.model.name }}</v-card-subtitle>
                    <v-col cols="12" class="px-6">
                        <v-text-field
                            color="blue-grey"
                            label="Name for merged validation"
                            :rules="[rules.isLongEnough(mergedValidation.name),
                                     rules.uniqueName(mergedValidation.name, nodeNeighbours)]"
                            v-model="mergedValidation.name"
                        ></v-text-field>
                    </v-col>
                    <v-col cols="12" class="px-6">
                        <v-text-field
                            color="blue-grey"
                            label="Notes to add to merged validation"
                            v-model="mergedValidation.notes"
                        ></v-text-field>
                    </v-col>
                <v-card-actions class="pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="blue-grey darken-2" text
                        @click="closeMergeDialog"
                    >
                        Close
                    </v-btn>
                    <v-btn color="primary" text
                        :disabled="!valid"
                        :loading="validationMergeLoading" @click="mergeValidation"
                    >
                        Merge
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
                showMergeDialog: true,
                mergedValidation: {name: '', notes: ''},
                validationMergeLoading: false,
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
            selectedNodes: { type: Array, required: true }
        },
        watch: {
            showMergeDialog(val) {
                this.closeMergeDialog()
            }
        },
        computed: {
            ...mapState('tree', ['validations']),
            branchInfo() {
                let info = []
                let current = this.selectedNodes[0].$parent
                while (current.model.level != 'gen') {
                    info.unshift(current.model.text)
                    current = current.$parent
                }
                return info.join(' / ')
            },
            nodeNeighbours() {
                return this.selectedNodes[0].$parent.$children.map(node => node.model.text)
            },
        },
        methods: {
            closeMergeDialog() {
                this.$emit('close')
            },
            mergeValidation() {
                this.validationMergeLoading = true
                const url = 'api/import/merge/'
                server
                    .post(url, {validation_name: this.mergedValidation.name,
                                 notes: this.mergedValidation.notes,
                                 validation_ids: this.validations})
                    .then(response => {
                        this.$toasted.success('Merging started in the background.<br>\n' +
                                              'You will be notified by email at the end.', { duration: 6000 })
                        this.closeMergeDialog()
                    })
                    .catch(error => {
                        if(error.response.status != 422) {
                            if (error.handleGlobally) {
                                error.handleGlobally('Failed to merge validations', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        } else {
                            let errors = error.response.data.errors.map(function(elem){ return elem.message }).join('<br>')
                            this.$toasted.global.alert_error(errors)
                        }
                    })
                    .finally(() => {
                        this.validationMergeLoading = false
                    })
            }
        },
    }
</script>
