<template>
    <v-card>
        <v-card-title class="gradient-create-bottom">
            <span style="font-size: 18px" class="body-1 font-weight-medium">
                <span class="title font-weight-bold">{{ objectName }}</span> object creation form
            </span>
        </v-card-title>
        <v-card-text class="mt-2">
            <span class="subtitle-1">Object will be created using data shown below</span>
            <template v-for="(value, key) in modelObject.fields">
                <v-text-field
                    readonly filled color="blue-grey"
                    :label="key"
                    :value="value"
                ></v-text-field>
            </template>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="red" text @click="closeDialog">Close</v-btn>
            <v-btn color="cyan darken-2" text @click="submit">Submit</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
    import server from '@/server.js'

    export default {
        data() {
            return {}
        },
        props: {
            modelObject: { type: Object, required: true },
            errorCode: { type: String, required: true },
            priority: { type: String, required: true },
            ID: { type: String, required: true }
        },
        computed: {
            objectName() {
                let model = this.modelObject.model;
                if (model == 'Item')
                    model = 'Test ' + model;
                return model;
            }
        },
        methods: {
            closeDialog() {
                this.$emit('closeCreate');
            },
            submit() {
                let data = { "entities": [{ "model": this.modelObject.model, "fields": {} }] }

                Object.keys(this.modelObject.fields).forEach(field => {
                    data["entities"][0]["fields"][field] = this.modelObject.fields[field];
                });

                const url = 'api/import/create/';
                server
                    .post(url, data)
                    .then(response => {
                        console.log(response);
                        this.$toasted.global.alert_success(`${this.modelObject.model} object was created`);

                        // remove error by ID from importErrors
                        this.$store.dispatch('deleteImportError', {id: this.ID, priority: this.priority, errorCode: this.errorCode})
                            .then(() => { this.$emit('closeCreate') }
                        )
                    })
                    .catch(error => {
                        if (error.response) {
                            if ('data' in error.response) {
                                console.log(error.response);
                                let returned = error.response.data;
                                this.$toasted.global.alert_error_detailed({
                                    'header': `Failed to create ${this.objectName} object<br>\n`,
                                    'message': `${returned.detail}<br>\nURL: ${server.defaults.baseURL}/${url}<br>\n${JSON.stringify(data)}`
                                })
                            }
                        } else if (error.request) {     // The request was made but no response was received
                            console.log('No response, request:', error.request);
                            this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                        } else {
                            console.log('Something happened in setting up the request that triggered an Error:', error.message);
                            this.$toasted.global.alert_error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                        }
                    })
                    .finally(() => {})
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