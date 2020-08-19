<template>
    <v-dialog :value="requestItemDialog" @input="closeRequestDialog" max-width="50%">
        <v-card>
            <v-card-title>
                New {{ model }} item creation request
            </v-card-title>
            <v-card-text class="text-body-1">
                <div> You are going to send request to administrators for {{ model }} item creation: </div>
                <v-form v-model="isFormValid" @submit.prevent>
                    <v-col cols="12" class="pt-0 pb-1" v-for="field in fields[model]" :key="model + field.label">
                        <v-text-field v-if="field.type == 'text'"
                            color="blue-grey"
                            :clearable="!disableInput(field)"
                            :readonly="disableInput(field)"
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
</template>

<script>
    import server from '@/server'
    import { mapState } from 'vuex'
    import { fields } from '@/store/request'
    import ApiAutoComplete from '@/components/APIAutoComplete'

    export default {
        components: {
            ApiAutoComplete,
        },
        data() {
            return {
                isFormValid: null,
                requestedItem: {},
                loading: false,
                isFormValid: null,
                sending: false,
                fields: fields,
            }
        },
        props: {
            model: { type: String, required: true },
            filling: { type: Object, required: false },
        },
        computed: {
            ...mapState(['userData']),
            ...mapState('request', ['requestItemDialog', 'rules']),
            disableInput() {
                return currentField => {
                    return !!this._.filter(Object.keys(this.filling), function(f) { return f == currentField.name}).length
                }
            }
        },
        methods: {
            closeRequestDialog() {
                this.$store.dispatch('request/setRequestDialogState', '')
                this.$nextTick(() => {
                    this.requestedItem = {}
                })
            },
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
                        this.$store.dispatch('request/setRequestDialogState', '')
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
        },
        beforeUpdate() {
            if (this.filling) {
                for (const field in this.filling) {
                    this.requestedItem[field] = this.filling[field]
                }
            }
        }
    }
</script>

<style>

</style>