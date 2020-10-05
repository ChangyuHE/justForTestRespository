<template>
    <v-autocomplete
        item-text="name"
        class="pt-2"
        color="blue-grey"
        loader-height="2"
        label="Select Feature Mappings to create the report"
        no-data-text="No appropritate mappings found"
        return-object hide-selected clearable multiple small-chips deletable-chips
        :items="items"
        :loading="loading"
        :error-messages="validationErrors"
        :menu-props="{closeOnContentClick: true}"
        :value="value"
        @input="emitInput"
        @change="onChange"
    >
        <template v-slot:append-outer>
            <v-tooltip bottom v-model="showTooltip">
                <template v-slot:activator="{ on }">
                    <v-icon size="20" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                </template>
                <router-link to="/feature-mapping" target="_blank">Mappings</router-link> searched by validation's Platform, OS and Component from all test-items executed during this validation.<br>
            </v-tooltip>
        </template>
    </v-autocomplete>
</template>

<script>
    import server from '@/server'

    export default {
        props: {
            value: {type: Array, required: true},
            items: {type: Array, required: true},
        },
        data() {
            return {
                loading: false,
                validationErrors: [],
                showTooltip: false,
                mappings: [],
            }
        },
        methods: {
            onChange(obj) {
                // emit v-autocomplete change event to parent
                this.$emit('change', obj)
                this.mappings = obj

                this.validationErrors = []
                if (!this.mappings.length)
                    return

                // validation of selected mappings
                if (this.mappings.length > 1) {
                    this.loading = true
                    const url = `api/feature_mapping/conflicts/?ids=${this._.map(this.mappings, 'id')}`
                    server
                        .get(url)
                        .then(response => {
                            if (!response.data) {
                                this.validationErrors.push('Only one feature mapping per codec on platform allowed')
                            } else {
                                this.$emit('validation-passed')
                            }
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Failed on feature mappings check', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                        .finally(() => this.loading = false)
                } else {
                    this.$emit('validation-passed')
                }
            },
            emitInput(obj) {
                this.$emit('input', obj)
            }
        }
    }
</script>
<style scoped>
    .v-application .v-tooltip__content a {
        color: rgb(247, 248, 201);
    }
    .v-tooltip__content {
        pointer-events: initial;
    }
</style>>