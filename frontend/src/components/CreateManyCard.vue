<template>
    <v-card>
       <v-card-title class="gradient-create-bottom">
            <span style="font-size: 18px" class="body-1 font-weight-medium">
                <span class="title font-weight-bold">{{ objectName }}</span> objects creation form
            </span>
        </v-card-title>
        <v-card-text class="pb-0">
            <div class="d-flex justify-space-between">
                <span class="subtitle-1 d-flex align-self-center ">A number of object will be created using data shown below</span>
                <div class="d-flex justify-end">
                    <v-btn color="red" text :disabled="sending" @click="closeDialog">Close</v-btn>
                    <v-btn color="cyan darken-2" text :loading="sending" @click="submit">Submit</v-btn>
                </div>
            </div>
            <hr>
            <v-list dense>
                <v-list-item v-for="(error, i) in errors" :key="i">
                    <v-list-item-content>
                        <span class="text-body-2" v-html="getMessage(error)"></span>
                        <v-divider class="mt-2" v-if="i != errors.length - 1"></v-divider>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
            <hr>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="red" text :disabled="sending" @click="closeDialog">Close</v-btn>
            <v-btn color="cyan darken-2" text :loading="sending" @click="submit">Submit</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
    import server from '@/server.js'

    export default {
        data() {
            return {
                sending: false
            }
        },
        props: {
            errors: { type: Array, required: true },
            errorCode: { type: String, required: true },
            priority: { type: String, required: true }
        },
        computed: {
            error() {
                return this.errors[0].entity
            },
            objectName() {
                let model = this.error.model
                if (model == 'Item') {
                    model = 'Test ' + model
                }
                return model
            }
        },
        methods: {
            getMessage(e) {
                let message = ''
                if (e.entity) {
                    for (let name in e.entity.fields)
                        message += `<b>${name}</b>: ${e.entity.fields[name]}<br>`
                }
                return message
            },
            closeDialog() {
                this.$emit('closeCreate')
            },
            submit() {
                this.sending = true
                let data = {'entities': []}
                for (let e of this.errors)
                    data.entities.push(e.entity)

                const url = 'api/import/create/'
                server
                    .post(url, data)
                    .then(response => {
                        this.$toasted.success(`${this.error.model} objects were created`)

                        // remove error group from importErrors
                        this.$store
                            .dispatch('deleteImportErrorsGroup', {priority: this.priority, errorCode: this.errorCode, model: this.error.model})
                            .then(() => this.$emit('closeCreate'))
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed to create ${this.objectName} objects`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.sending = false)
            }
        }
    }
</script>

<style scoped>
    .gradient-create-bottom {
        border-bottom: 3px solid transparent;
        border-image-source: linear-gradient(to right, #00897B, #4DD0E1);
        border-image-slice: 1;
    }
</style>