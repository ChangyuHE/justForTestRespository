<template>
    <v-card flat class="d-flex">
        <v-col cols="8" class="d-flex flex-column">
            <span class="body-1 font-weight-medium">
                <span v-if="error.entity" class="font-weight-black">
                    {{ objectName }}
                </span>
                {{ description }}
            </span>
            <span v-html="message" class="subtitle-2 font-weight-regular d-inline-block text-truncate">
            </span>
        </v-col>

        <v-col class="d-flex justify-end">
            <!-- Create item dialog -->
            <v-dialog v-if="canBeCreated"
                v-model="createItemDialog"
                persistent max-width="50%"
            >
                <template v-slot:activator="{ on }">
                    <v-btn small v-on="on">Create</v-btn>
                </template>

                <create-item-card
                    :model-object="error.entity"
                    :priority="priority"
                    :error-code="errorCode"
                    :ID="error.ID"
                    @closeCreate="createItemDialog = false"
                ></create-item-card>
            </v-dialog>

            <!-- Request item creation -->
            <v-dialog v-if="mustBeRequested"
                v-model="requestItemDialog"
                persistent max-width="50%"
            >
                <template v-slot:activator="{ on }">
                    <v-btn small v-on="on">Request creation</v-btn>
                </template>

                <v-card>
                    <v-card-title>
                        New {{ error.entity.model }} item creation request
                    </v-card-title>
                    <v-card-text class="text-body-1">
                        <div> You are going to send request to administrators for {{ error.entity.model }} item creation </div>
                        <div> New values: </div>
                        <div v-for="(value, key) in error.entity.fields" :key="key">
                            - {{ key }} : {{ value }}
                        </div>
                    </v-card-text>
                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn
                            color="green" text
                            @click="sendRequest"
                            :loading="sending"
                        >
                            Send
                        </v-btn>
                        <v-btn
                            color="red" text
                            @click="requestItemDialog = false"
                            :disabled="sending"
                        >
                            Close
                        </v-btn>
                    </v-card-actions>
                </v-card>

            </v-dialog>
        </v-col>
    </v-card>
</template>

<script>
    import server from '@/server'
    import createItemCard from '@/components/CreateItemCard'

    const ERR_CODE_MAPPING = {
        'ERR_MISSING_ENTITY': 'object not found in DB',
        'ERR_INVALID_VALIDATION_ID': 'No validation with given ID found',
        'ERR_MISSING_COLUMNS': 'Mandatory column(s) not found in importing file',
        'ERR_WORKBOOK_EXCEPTION': 'Couldn\'t process Excel file',
        'ERR_DATE_FORMAT': 'Couldn\'t convert date format from input file',
        'ERR_EXISTING_VALIDATION': 'Validation duplicate is going to be imported',
        'ERR_AMBIGUOUS_COLUMN': 'Non-unique values in column',
        'ERR_EXISTING_RUN': 'Using already imported run'
    }

    const CAN_BE_CREATED = ['Driver', 'Item']
    const MUST_BE_REQUESTED = ['Component', 'Env', 'Platform', 'Os', 'Status', 'Generation']

    export default {
        components: {
            createItemCard
        },
        data() {
            return {
                createItemDialog: null,
                requestItemDialog: null,
                sending: false,
            }
        },
        props: {
            error: { type: Object, required: true },
            priority: { type: String, required: true },
            errorCode: { type: String, required: true },
        },
        computed: {
            objectName() {
                let model = this.error.entity.model;
                if (model == 'Item')
                    model = 'Test ' + model;
                return model;
            },
            canBeCreated() {
                if (this.error.entity)
                    return CAN_BE_CREATED.includes(this.error.entity.model);
                return false;
            },
            mustBeRequested() {
                if (this.error.entity) {
                    return MUST_BE_REQUESTED.includes(this.error.entity.model)
                } else {
                    return false;
                }
            },
            description() {
                return ERR_CODE_MAPPING[this.errorCode]
            },
            message() {
                let message = this.error.message;
                if (this.errorCode == 'ERR_AMBIGUOUS_COLUMN') {
                    if (this.error.values)
                        message = `${message} <b><i>"${this.error.column}"</i> : ${this.error.values.join(', ')}</b>`
                } else if (this.errorCode == 'ERR_MISSING_COLUMNS') {
                    if (this.error.values)
                        message += `<br>Missing columns: <b>${this.error.values}</b>`
                } else if (this.errorCode == 'ERR_EXISTING_VALIDATION') {
                    message += ":<br>"
                    if (this.error.entity)
                        for (let name in this.error.entity.fields)
                            message += `\t<b>${name}: ${this.error.entity.fields[name]}</b><br>`;
                } else if (this.errorCode == 'ERR_MISSING_ENTITY') {
                    message = '';
                    if (this.error.entity)
                        for (let name in this.error.entity.fields)
                            message += `${name}: ${this.error.entity.fields[name]}<br>`
                }
                return message;
            },
        },
        methods: {
            sendRequest() {
                this.sending = true;
                let currentUserUrl = 'api/users/current/';
                let url = 'api/objects/create/';
                let currentUser = {};
                server
                    .get(currentUserUrl)
                    .then(userInfo => {
                        currentUser = userInfo.data;
                        let data = {model: this.error.entity.model, fields: this.error.entity.fields, requester: currentUser}
                        return server.post(url, data);
                    })
                    .then(response => {
                        this.requestItemDialog = false;
                        this.$toasted.success('Request has been sent');
                    })
                    .catch(error => {
                        error.handleGlobally('Error during requesting creation of a new object', url)
                    })
                    .finally(() => (this.sending = false))
            }
        }
    }
</script>