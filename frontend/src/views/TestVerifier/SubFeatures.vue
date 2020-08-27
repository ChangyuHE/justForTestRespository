<template>
    <v-card class="mb-2">
        <!-- Subfeatures table -->
        <v-data-table class="subfeatures"
            hide-default-header
            :headers="headers"
            :items="subFeatures"
            :search="search"
            :loading="loading"
            :sort-by.sync="sortBy"
            :sort-desc.sync="sortDesc">
            <template v-slot:top>
                <v-toolbar flat>
                    <!-- Generations buttons group -->
                    <v-btn-toggle
                        class="mt-2"
                        color="blue-grey"
                        multiple
                        v-model="selectedGenerations"
                        @change="changeGens()">
                        <!-- Dropdown buttons for show Platforms list -->
                        <v-menu open-on-hover offset-y v-for="gen in generations" :key="gen.name" :close-on-content-click="false">
                            <template v-slot:activator="{ on }">
                                <v-btn
                                    v-on="on"
                                    class="outlined"
                                    small
                                    :value="gen"
                                    @click="changeGen(gen)">
                                    {{ gen.name }}
                                </v-btn>
                            </template>
                            <v-list>
                                <v-list-item-group>
                                    <v-list-item v-for="platform in platformsByGen[gen.name]" :key="platform.id">
                                        <v-list-item-content class="pa-0">
                                            <v-checkbox
                                                small
                                                class="platform-filter ma-0"
                                                v-model="selectedPlatforms"
                                                :label="platform.short_name"
                                                :value="platform.id"
                                                @change="changePlatform(gen, platform)"
                                                hide-details></v-checkbox>
                                        </v-list-item-content>
                                    </v-list-item>
                                </v-list-item-group>
                            </v-list>
                        </v-menu>
                    </v-btn-toggle>
                    <v-spacer></v-spacer>
                    <v-col cols="3">
                        <!-- Subfeatures searchbox -->
                        <v-text-field
                            class="pt-0 mt-0 mr-3"
                            color="teal"
                            v-model="search"
                            append-icon="mdi-magnify"
                            label="Search"
                            hide-details
                            clearable
                        ></v-text-field>
                    </v-col>
                    <!-- Subfeature creation/edition dialog -->
                    <v-dialog v-model="dialog" max-width="800px">
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn fab dark small
                                color="teal"
                                class="mb-2"
                                v-bind="attrs"
                                v-on="on">
                                    <v-icon dark>mdi-plus</v-icon>
                            </v-btn>
                        </template>
                        <v-card>
                            <v-card-title>
                                <span class="headline">{{ formTitle }}</span>
                            </v-card-title>
                            <v-card-text>
                                <v-container>
                                    <v-form
                                        v-model="valid">
                                        <v-row>
                                            <v-col cols="12">
                                                <v-text-field
                                                    color="teal"
                                                    v-model="editedSubfeature.name"
                                                    label="SubFeature"
                                                    :rules="[rules.required]"
                                                    return-object
                                                    clearable
                                                    required>
                                                </v-text-field>
                                            </v-col>
                                            <v-col cols="12" sm="6" md="4">
                                                <v-autocomplete
                                                    color="teal"
                                                    :items="codecs"
                                                    label="Codec"
                                                    v-model="editedSubfeature.codec"
                                                    item-text="name"
                                                    return-object
                                                    :rules="[rules.required]"
                                                    placeholder="Start typing to filter values"
                                                    required>
                                                </v-autocomplete>
                                            </v-col>
                                            <v-col cols="12" sm="6" md="4">
                                                <v-autocomplete
                                                    color="teal"
                                                    :items="featureCategories"
                                                    label="Feature Category"
                                                    v-model="editedSubfeature.category"
                                                    item-text="name"
                                                    return-object
                                                    placeholder="Start typing to filter values"
                                                    :rules="[rules.required]"
                                                    required>
                                                </v-autocomplete>
                                            </v-col>
                                            <v-col cols="12" sm="6" md="4">
                                                <v-autocomplete
                                                    color="teal"
                                                    :items="features"
                                                    label="Feature"
                                                    v-model="editedSubfeature.feature"
                                                    item-text="name"
                                                    return-object
                                                    placeholder="Start typing to filter values"
                                                    :rules="[rules.required]"
                                                    required>
                                                </v-autocomplete>
                                            </v-col>
                                        </v-row>
                                        <v-divider></v-divider>
                                        <v-row>
                                            <v-col cols="12" class="mt-0">
                                                <v-simple-table>
                                                    <template v-slot:default>
                                                    <thead>
                                                        <tr>
                                                            <th class="text-left">Feature Support</th>
                                                            <th class="text-left">Platforms</th>
                                                            <th></th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr>
                                                            <td>{{ oses.LINUX_OS }}</td>
                                                            <td>
                                                                <div class="platforms">
                                                                    <span class="platform" v-for="platform in editedSubfeature.lin_platforms" :key="platform.id">{{ platform.short_name }}</span>
                                                                </div>
                                                            </td>
                                                            <td>
                                                                <v-icon class="mr-2" small @click="editPlatforms(oses.LINUX_OS)">mdi-pencil</v-icon>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td>{{ oses.WINDOWS_OS }}</td>
                                                            <td>
                                                                <div class="platforms">
                                                                    <span class="platform" v-for="platform in editedSubfeature.win_platforms" :key="platform.id">{{ platform.short_name }}</span>
                                                                </div>
                                                            </td>
                                                            <td>
                                                                <v-icon class="mr-2" small @click="editPlatforms(oses.WINDOWS_OS)">mdi-pencil</v-icon>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                    </template>
                                                </v-simple-table>
                                            </v-col>
                                        </v-row>
                                    </v-form>
                                </v-container>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="teal" text @click="close">Cancel</v-btn>
                                <v-btn color="teal" text @click="save" :disabled="!valid">Save</v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <!-- Platforms adding dialog -->
                    <v-dialog persistent v-model="dialogPlatforms" max-width="600px">
                        <v-card>
                            <v-card-title>
                                <span>Feature Platforms for {{ selectedOS }}</span>
                                <v-spacer></v-spacer>
                            </v-card-title>
                            <v-container>
                                <v-row>
                                    <v-col cols="12">
                                        <v-autocomplete
                                            color="teal"
                                            chips
                                            multiple
                                            :items="platforms"
                                            label="Platforms"
                                            v-model="editedPlatforms"
                                            return-object
                                            placeholder="Start typing to filter values"
                                            item-text="short_name">
                                        </v-autocomplete>
                                    </v-col>
                                </v-row>
                            </v-container>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="teal" text @click="closePlatforms">Close</v-btn>
                                <v-btn color="teal" text @click="addPlatforms">Add</v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-toolbar>
            </template>
            <!-- Subfeatures Table's header -->
            <template v-slot:header="{ props: { headers } }" >
                <thead class="v-data-table-header">
                    <tr>
                        <th v-for="header in headers"
                            :key="header.text"
                            :rowspan="header.rowspan"
                            :colspan="header.value == 'platform' ? getColspanForSupport() : 1"
                            :class="[header.class, 'sortable', sortDesc ? 'desc' : 'asc', header.value === sortBy ? 'active' : '']"
                            @click="toggleOrder(header)">
                                <span>{{ header.text }}</span>
                                <v-icon class="v-data-table-header__icon" v-if="header.sortable !== false" small>mdi-arrow-up</v-icon>
                        </th>
                    </tr>
                    <tr>
                        <!-- Generation row -->
                        <template v-for="gen in selectedGenerations">
                            <th :colspan="getColspanForGen(gen)" class="generation pa-0"  :key="gen.name" v-if="getColspanForGen(gen)">
                                {{ gen.name }}
                            </th>
                        </template>
                    </tr>
                    <tr>
                        <!-- Platforms row -->
                        <template v-for="gen in selectedGenerations">
                            <template v-for="platform in platformsByGen[gen.name]">
                                <template v-if="isSelectedPlatform(platform)">
                                    <th colspan="2" class="col-platform"  :key="platform.id">
                                        <span>{{ platform.short_name }}</span>
                                    </th>
                                </template>
                            </template>
                        </template>
                    </tr>
                    <tr>
                        <!-- Os row -->
                        <template v-for="gen in selectedGenerations">
                            <template v-for="platform in platformsByGen[gen.name]">
                                <th class="col-os" :key="'win_'+platform.id" v-if="isSelectedPlatform(platform)">
                                    <v-icon small :title="oses.WINDOWS_OS">mdi-microsoft-windows</v-icon>
                                </th>
                                <th class="col-os" :key="'lin_'+platform.id" v-if="isSelectedPlatform(platform)">
                                    <v-icon small :title="oses.LINUX_OS">mdi-linux</v-icon>
                                </th>
                            </template>
                        </template>
                    </tr>
                </thead>
            </template>
            <!-- Subfeatures Body's header -->
            <template v-slot:item="{ item, index }">
                <tr class="subfeature" v-if="isShow(item)">
                    <td>{{ item.codec.name }}</td>
                    <td>{{ item.category.name }}</td>
                    <td>{{ item.feature.name }}</td>
                    <td>{{ item.name }}</td>
                    <template v-for="gen in selectedGenerations">
                        <template v-for="platform in platformsByGen[gen.name]">
                            <template v-if="isSelectedPlatform(platform)">
                                <td class="pa-0 supporting" v-for="os in oses" :key="os+platform.id" :value="support = checkSupport(item, os, platform)">
                                    <span :class="support">{{support}}</span>
                                </td>
                            </template>
                        </template>
                    </template>
                    <td>
                        <v-hover v-slot:default="{ hover }">
                            <v-icon class="mr-2" small :class="{ 'primary--text': hover }" @click="editSubfeatures(item, index)">mdi-pencil</v-icon>
                        </v-hover>
                        <v-hover v-slot:default="{ hover }">
                            <v-icon small :class="{ 'red--text': hover }" @click="openDeleteDialog(item)">mdi-delete</v-icon>
                        </v-hover>
                    </td>
                </tr>
            </template>
        </v-data-table>
        <!-- Subfeature deleting dialog -->
        <v-dialog v-model="dialogDelete" max-width="500px">
            <v-card>
                <v-card-title>Delete subfeature</v-card-title>
                <v-card-text>Are you sure you want to delete {{ subfeatureToDelete.name }} subfeature?</v-card-text>
                <v-card-actions>
                <v-btn color="primary" text @click="dialogDelete = false">Close</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="red" text @click="deleteSubfeature()">Delete</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-card>
</template>

<script>
    import server from '@/server'

    const oses = Object.freeze({
        WINDOWS_OS: 'Windows',
        LINUX_OS: 'Linux'
    })
    const url = 'test_verifier/features_data/'

    export default {
        data() {
            return {
                url,
                oses,
                search: '',
                loading: false,
                headers: [],
                sortBy: 'name',
                sortDesc: false,
                valid: true,
                dialog: false,
                dialogPlatforms: false,
                dialogDelete: false,
                rules: {
                    required: value => !!value || 'Required.'
                },

                codecs: [],
                featureCategories: [],
                features: [],
                generations: [],
                platforms: [],
                platformsByGen: {},
                subFeatures: [],

                selectedGenerations: [],
                selectedPlatforms: [],
                selectedOS: oses.WINDOWS_OS,
                editedIndex: -1,
                editedSubfeature: {
                    'win_platforms': [],
                    'lin_platforms': [],
                },
                defaultSubfeature: {
                    'win_platforms': [],
                    'lin_platforms': [],
                },
                subfeatureToDelete: {},
                editedPlatforms: [],
            }
        },
        computed: {
            formTitle() {
                return this.editedIndex == -1 ? 'New Subfeature' : 'Edit Subfeature'
            },
        },
        watch: {
            dialog(val) {
                val || this.close()
            },
            dialogPlatforms(val) {
                val || this.closePlatforms()
            },
            dialogDelete(val) {
                val || this.closeDeleteDialog()
            },
        },
        methods: {
            toggleOrder (header) {
                // Header sorting for Data Table
                this.sortDesc = !this.sortDesc
                this.sortBy = header.value
            },
            uniq(arr) {
                return arr.filter((v, i, a) => a.findIndex(t => (JSON.stringify(t) === JSON.stringify(v))) === i)
            },
            sortNumeric(arr) {
                return arr.slice().sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))
            },
            platformKey(os) {
                return `${os.substring(0, 3).toLowerCase()}_platforms`
            },
            getColspanForSupport() {
                // Dynamic column for all supporting platforms
                // 2* - For Windows and Linux
                return 2 * this._.reduce(this.selectedGenerations, (result, gen) => {
                    let platforms = this.platformsByGen[gen.name].filter((item) => this.isSelectedPlatform(item))
                    return platforms.length + result
                }, 0)
            },
            getColspanForGen(gen) {
                // Dynamic column for supporting platforms inside generation
                let platforms = this.platformsByGen[gen.name].filter((item) => this.isSelectedPlatform(item))
                return platforms.length * 2
            },
            isSelectedPlatform(platform) {
                return this.selectedPlatforms.indexOf(platform.id) >= 0
            },
            isShow(subfeature) {
                // Subfeature that are not supported in the selected filters are not shown
                if (this.selectedGenerations.length == this.generations.length &&
                    this.selectedPlatforms.length == this.platforms.length) {
                    return true
                } else {
                    let win_platforms = subfeature.win_platforms.filter((item) => this.selectedPlatforms.indexOf(item.id) >= 0)
                    let lin_platforms = subfeature.lin_platforms.filter((item) => this.selectedPlatforms.indexOf(item.id) >= 0)
                    return win_platforms.length || lin_platforms.length
                }
            },
            changeGens() {
                // Sorting generations after toggle filters
                this.selectedGenerations = this.sortNumeric(this.selectedGenerations)
            },
            changeGen(gen) {
                // Remove/Add platform by Gen toggle
                let selectedPlatformsWithoutGen = this.platforms.filter((item) => {
                    return item.generation.name != gen.name && this.selectedPlatforms.indexOf(item.id) >= 0
                    }).map((item) => item.id)
                let genPlatforms = this.platformsByGen[gen.name].map((item) => item.id)
                if (this._.intersection(this.selectedPlatforms, genPlatforms).length != 0) {
                    this.selectedPlatforms = selectedPlatformsWithoutGen
                } else {
                    this.selectedPlatforms = this._.flatten([selectedPlatformsWithoutGen, genPlatforms])
                }
            },
            changePlatform(gen, platform) {
                let genIndex = this._.findIndex(this.selectedGenerations, {name: platform.generation.name})
                if (genIndex < 0 && this.selectedPlatforms.indexOf(platform.id) >= 0) {
                    this.selectedGenerations.push(gen)
                    this.selectedGenerations = this.sortNumeric(this.selectedGenerations)
                } else {
                    let platformsByGen = this.platformsByGen[platform.generation.name].map((item) => item.id)
                    if (this._.intersection(platformsByGen, this.selectedPlatforms).length === 0) {
                        this.selectedGenerations.splice(genIndex, 1)
                    }
                }
            },
            getSubFeatures() {
                this.loading = true
                server
                    .get(this.url)
                    .then(featuresData => {
                        this.subFeatures = featuresData.data
                        this.headers = [
                            { text: 'Codec', rowspan: 4, class: 'col-codec', value: 'codec.name' },
                            { text: 'Feature Category', rowspan: 4, class: 'col-category', value: 'category.name' },
                            { text: 'Feature', rowspan: 4, class: 'col-feature', value: 'feature.name' },
                            { text: 'Sub Feature', rowspan: 4, value: 'name' },
                            { text: '', value: "platform", class: 'col-support', sortable: false },
                            { text: 'Actions', rowspan: 4, class: 'col-actions' },
                        ]
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during getting of features', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.loading = false)
            },
            checkSupport(item, os, platform) {
                let item_platform = item[this.platformKey(os)].filter((p) => p.id == platform.id)
                return item_platform.length ? 'y' : 'n'
            },
            addPlatforms() {
                this.editedSubfeature[this.platformKey(this.selectedOS)] = this.editedPlatforms
                this.dialogPlatforms = false
            },
            editPlatforms(os) {
                this.dialogPlatforms = !this.dialogPlatforms
                this.selectedOS = os
                this.editedPlatforms = this.editedSubfeature[this.platformKey(os)]
            },
            editSubfeatures(item, index) {
                this.editedIndex = index
                this.editedSubfeature = Object.assign({}, item)
                this.dialog = true
            },
            openDeleteDialog(item) {
                this.subfeatureToDelete = item
                this.dialogDelete = !this.dialogDelete
            },
            deleteSubfeature() {
                server
                    .delete(`${url}${this.subfeatureToDelete.id}/`)
                    .then(response => {
                        let index = this._.findIndex(this.subFeatures, {id: this.subfeatureToDelete.id})
                        this.subFeatures.splice(index, 1)
                        this.$toasted.success('Subfeature has been removed')
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Error during deletion', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.closeDeleteDialog())
            },
            close() {
                this.dialog = false
                this.$nextTick(() => {
                    this.editedSubfeature = Object.assign({}, this.defaultSubfeature)
                    this.editedIndex = -1
                })
            },
            closePlatforms() {
                this.dialogPlatforms = false
                this.$nextTick(() => {
                    this.editedPlatforms = []
                })
            },
            closeDeleteDialog() {
                this.dialogDelete = false
                this.$nextTick(() => {
                    this.subfeatureToDelete = {}
                })
            },
            save() {
                let sfSaving = {
                    name: this.editedSubfeature.name,
                    codec: this.editedSubfeature.codec.id,
                    category: this.editedSubfeature.category.id,
                    feature: this.editedSubfeature.feature.id,
                    lin_platforms: this.editedSubfeature.lin_platforms.map((item) => item.id),
                    win_platforms: this.editedSubfeature.win_platforms.map((item) => item.id),
                    imported: this.editedSubfeature.imported,
                    created: this.editedSubfeature.created,
                    created_by: this.editedSubfeature.created_by,
                    updated: this.editedSubfeature.updated,
                    updated_by: this.editedSubfeature.updated_by,
                }

                if (this.editedIndex > -1) {
                    server
                        .put(`${url}${this.editedSubfeature.id}/`, sfSaving)
                        .then(response => {
                            Object.assign(this.subFeatures[this.editedIndex], response.data)
                            this.close()
                            this.$toasted.success('Subfeature has been edited')
                        })
                        .catch(error => {
                            this.close()
                            if (error.handleGlobally) {
                                error.handleGlobally('Error during requesting edition of this object', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                } else {
                    server
                        .post(this.url, sfSaving)
                        .then(response => {
                            this.editedSubfeature.id = response.data.id
                            this.subFeatures.unshift(response.data)
                            this.close()
                            this.$toasted.success('Subfeature has been created')
                        })
                        .catch(error => {
                            this.close()
                            if (error.handleGlobally) {
                                error.handleGlobally('Error during requesting creation of a new object', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                }
            },
        },
        created() {
            // Initial codecs, categories, features, platforms
            let url = 'test_verifier/codecs/'
            server
                .get(url)
                .then(response => {
                    this.codecs = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get codecs', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
            url = 'test_verifier/categories/'
            server
                .get(url)
                .then(response => {
                    this.featureCategories = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get categories', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
            url = 'test_verifier/features/'
            server
                .get(url)
                .then(response => {
                    this.features = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get features', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
            url = 'api/platform/'
            server
                .get(url)
                .then(response => {
                    this.platforms = response.data
                    let generations = this.uniq(response.data.map((item) => item.generation))
                    this.generations = this.sortNumeric(generations)
                    this.selectedGenerations = [...this.generations].slice(-3)
                    let genIds = this.selectedGenerations.map((item) => item.id)
                    this.selectedPlatforms = response.data.filter((item) => genIds.indexOf(item.generation.id) >= 0).map((item) => item.id)
                    this.platformsByGen = this._.reduce(response.data, (result, item) => {
                        if (result[item.generation.name]) {
                            result[item.generation.name].push(item)
                        } else {
                            result[item.generation.name] = [item]
                        }
                        return result
                    }, {})
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get platforms', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
        },
        mounted() {
            this.getSubFeatures()
        }
    }
</script>

<style>
    .subfeatures th {
        border: thin solid rgba(0, 0, 0, 0.12);
    }
    .subfeatures .col-codec, .col-category, .col-feature, .col-actions {
        width: 170px;
    }
    .subfeatures .col-support {
        border-bottom: 0;
        height: 0px !important;
    }
    .subfeatures .col-support span {
        display: flex;
        justify-content: center;
    }
    .subfeatures .col-platform {
        padding: 0px !important;
        text-align: center !important;
    }
    .subfeatures .col-platform span {
        font-size: 13px;
    }
    .subfeatures .col-os {
        height: 35px !important;
        padding: 0px !important;
        text-align: center !important;
        width: 35px;
    }
    .subfeatures .platforms {
        display: flex;
        flex-wrap: wrap;
        padding: 2px;
    }
    .platforms .platform {
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 3px;
        color: #222222;
        cursor: default;
        display: inline;
        font-size: 11px;
        margin: 2px;
        padding: 3px;
        word-break: break-all;
    }
    .subfeatures .generation {
        height: 25px !important;
        text-align: center !important;
    }
    .subfeatures .supporting span {
        border-left: thin solid rgba(0, 0, 0, 0.12);
        display: block;
        font-size: 12px;
        height: 100%;
        padding-top: 5px;
        text-align: center;
        text-transform: uppercase;
        width: 100%;
    }
    .subfeatures .supporting .y {
        background-color: #C6E0B4;
    }
    .subfeatures .supporting .n {
        background-color: #FFF2CC;
    }
    .subfeatures .platform-filter label {
        font-size: 14px;
    }
</style>