<template>
    <v-autocomplete v-if="type == 'sync'"
        class="api-auto-complete"
        item-text="name"
        item-value="id"
        prepend-icon="mdi-database-search"
        placeholder="Start typing to get values"
        return-object hide-no-data hide-selected clearable hide-details
        :disabled="disabled"
        :label="modelName"
        :color="color"
        :items="items"
        :loading="isLoading"
        :search-input.sync="search"
        :value="value"
        :rules="rules"
        @input="emit"
    ></v-autocomplete>
    <v-autocomplete v-else
        class="api-auto-complete"
        item-text="name"
        return-object hide-no-data hide-selected clearable hide-details
        :disabled="disabled"
        :label="modelName"
        :color="color"
        :items="items"
        :loading="isLoading"
        :value="value"
        :rules="rules"
        :error-messages="errorMessages"
        @input="emit"
      ></v-autocomplete>
</template>

<script>
    import server from '@/server'

    export default {
        props: {
            value: {required: true},
            rules: {type: Array, required: false},
            modelName: {type: String, required: true},
            color: {type: String, required: false},
            disabled: {type: Boolean, required: false},
            type: {
                type: String,
                required: true,
                validator(value) {
                    // The value must match one of these strings
                    return ['sync', 'defined'].indexOf(value) !== -1
                }
            }
        },
        data() {
            return {
                selected: null,
                entries: [],
                search: null,
                isLoading: false,
                uploading: false,
                errorMessages: ''
            }
        },
        computed: {
            items() {
                return this.entries.map(entry => {
                    let name = entry.name
                    if (this.modelName == 'platform')
                        name = entry.short_name
                    return Object.assign({}, entry, { name })
                })
            },
        },
        methods: {
            emit(obj) {
                this.$emit('input', obj)
            },
            apiCall() {
                const url = `api/${this.modelName}/`
                server
                    .get(url)
                    .then(res => {
                        this.entries = res.data
                    })
                    .catch(error => {
                        error.handleGlobally && error.handleGlobally(`Could not get ${this.modelName} model data`, url)
                    })
                    .finally(() => (this.isLoading = false))
            }
        },
        watch: {
            search(val) {
                if (this.items.length > 0) return       // Items have already been loaded
                if (this.isLoading) return              // Items have already been requested
                this.isLoading = true

                this.apiCall()
            }
        },
        created() {
            // fill selector choices with data from api call on created
            if (this.type == 'defined')
                this.apiCall()
        }
    }
</script>

<style scoped>
    .api-auto-complete >>> .v-label {
        text-transform: capitalize;
    }
</style>