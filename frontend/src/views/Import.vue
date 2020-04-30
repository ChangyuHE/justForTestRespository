<template>
    <v-container fluid>
        <v-row>
            <v-col cols="6" class="pt-0">
                <v-file-input
                    full-width
                    v-model="file"
                    label="Select File to import"
                    show-size counter
                    class="pt-0"
                ></v-file-input>

                <v-autocomplete
                    v-model="selected"
                    :items="items"
                    :loading="isLoading"
                    :search-input.sync="search"
                    hide-no-data
                    hide-selected
                    item-text="name"
                    item-value="id"
                    label="Validaions"
                    placeholder="Start typing to search available validations"
                    prepend-icon="mdi-database-search"
                    return-object
                    clearable
                ></v-autocomplete>
            </v-col>
        </v-row>
        <v-btn :disabled="uploadDisabled" color="teal lighten-1" @click="onUpload">Upload</v-btn>
    </v-container>
</template>

<script>
    import server from '@/server';

    export default {
        data() {
            return {
                file: null,

                descriptionLimit: 100,
                entries: [],
                isLoading: false,
                selected: {'id': 0, 'name': 'new'},
                search: null,
            }
        },
        computed: {
            uploadDisabled() {
                return !Boolean(this.file)
            },
            items() {
                return this.entries.map(entry => {
                    const name = entry.name.length > this.descriptionLimit
                        ? entry.name.slice(0, this.descriptionLimit) + '...'
                        : entry.name
                    return Object.assign({}, entry, { name })
                    })
            },
        },
        watch: {
            search(val) {
                // Items have already been loaded
                if (this.items.length > 0) return

                // Items have already been requested
                if (this.isLoading) return

                this.isLoading = true

                // Lazily load input items
                //fetch('https://api.publicapis.org/entries')
                const url = 'api/validations/flat';
                server
                    .get(url)
                    // .then(res => res.json())
                    .then(res => {
                        // const { count, entries } = res
                        // this.count = count
                        // this.entries = entries
                        this.entries = res.data
                        console.log(res.data[0])
                    })
                    .catch(err => {
                        console.log(err)
                    })
                    .finally(() => (this.isLoading = false))
            },
        },
        methods: {
            onUpload() {
                console.log(this.selected);
                let id = null;
                if ('id' in this.selected)
                    id = this.selected.id;

                let formData = new FormData();
                formData.append('file', this.file);
                formData.append('validation_id', +id);

                const url = `api/import/`;
                server.put(url, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}
                })
                .then(response => {
                    console.log(response);
                })
                .catch(error => {
                    console.log(error);
                    this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                });
            }
        }
    }
</script>

<style>

</style>