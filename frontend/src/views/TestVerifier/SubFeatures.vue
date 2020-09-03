<template>
    <v-card class="mb-2">
        <v-tabs v-model="componentTab">
            <v-tabs-slider></v-tabs-slider>
            <v-tab
                v-for="comp in components"
                :key="comp.id"
                :href="`#${comp.id}`"
                @click="getSubfeaturesByComponent(comp.id)">
                {{ comp.name }}
            </v-tab>
            <!-- Subfeature creation/edition dialog -->
            <v-dialog v-model="dialog" max-width="800px">
                <template v-slot:activator="{ on, attrs }">
                    <v-btn dark small
                        color="teal"
                        class="add-subfeature"
                        v-bind="attrs"
                        v-on="on">
                            Add subfeature
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
                                            v-model="selectedSubfeature.name"
                                            label="SubFeature"
                                            :rules="[rules.required]"
                                            return-object
                                            clearable
                                            required>
                                        </v-text-field>
                                    </v-col>
                                    <v-col cols="12" sm="6" md="6">
                                        <v-autocomplete
                                            color="teal"
                                            :items="components"
                                            label="Component"
                                            v-model="selectedSubfeature.component"
                                            item-text="name"
                                            return-object
                                            :rules="[rules.required]"
                                            placeholder="Start typing to filter values"
                                            required>
                                        </v-autocomplete>
                                    </v-col>
                                    <v-col cols="12" sm="6" md="6">
                                        <v-autocomplete
                                            color="teal"
                                            :items="codecs"
                                            label="Codec"
                                            v-model="selectedSubfeature.codec"
                                            item-text="name"
                                            return-object
                                            :rules="[rules.required]"
                                            placeholder="Start typing to filter values"
                                            required>
                                        </v-autocomplete>
                                    </v-col>
                                    <v-col cols="12" sm="6" md="6">
                                        <v-autocomplete
                                            color="teal"
                                            :items="featureCategories"
                                            label="Feature Category"
                                            v-model="selectedSubfeature.category"
                                            item-text="name"
                                            return-object
                                            placeholder="Start typing to filter values"
                                            :rules="[rules.required]"
                                            required>
                                        </v-autocomplete>
                                    </v-col>
                                    <v-col cols="12" sm="6" md="6">
                                        <v-autocomplete
                                            color="teal"
                                            :items="features"
                                            label="Feature"
                                            v-model="selectedSubfeature.feature"
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
                                                            <span class="platform" v-for="platform in selectedSubfeature.lin_platforms" :key="platform.id">{{ platform.short_name }}</span>
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
                                                            <span class="platform" v-for="platform in selectedSubfeature.win_platforms" :key="platform.id">{{ platform.short_name }}</span>
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
            <v-tab-item
                v-for="comp in components"
                :key="comp.id"
                :value="`${comp.id}`">
                <v-card flat tile>
                    <v-toolbar flat height="84px">
                    <!-- Generations buttons group -->
                        <div>
                            <v-btn-toggle
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
                            <v-btn-toggle
                                class="mt-2 d-block"
                                color="blue-grey"
                                multiple
                                v-model="selectedCodecs">
                                <v-btn small v-for="codec in codecs" :key="codec.id" :value="codec.id">
                                    {{ codec.name }}
                                </v-btn>
                            </v-btn-toggle>
                        </div>
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
                    </v-toolbar>
                    <!-- Subfeatures table -->
                    <v-data-table class="subfeatures"
                        hide-default-header
                        :headers="headers"
                        :items="subFeaturesByComponent"
                        :search="search"
                        :loading="loading"
                        :sort-by.sync="sortBy"
                        :sort-desc.sync="sortDesc">
                        <template v-slot:top>
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
                        <!-- Subfeatures Body's row -->
                        <template v-slot:item="{ item }">
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
                                        <v-icon class="mr-2" small :class="{ 'primary--text': hover }" @click="openInfoDialog(item)">mdi-information</v-icon>
                                    </v-hover>
                                    <v-hover v-slot:default="{ hover }">
                                        <v-icon class="mr-2" small :class="{ 'primary--text': hover }" @click="editSubfeatures(item)">mdi-pencil</v-icon>
                                    </v-hover>
                                    <v-hover v-slot:default="{ hover }">
                                        <v-icon small :class="{ 'red--text': hover }" @click="openDeleteDialog(item)">mdi-delete</v-icon>
                                    </v-hover>
                                </td>
                            </tr>
                        </template>
                    </v-data-table>
                </v-card>
            </v-tab-item>
        </v-tabs>
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
        <!-- Subfeature deleting dialog -->
        <v-dialog v-model="dialogDelete" max-width="500px">
            <v-card>
                <v-card-title>Delete subfeature</v-card-title>
                <v-card-text>Are you sure you want to delete {{ selectedSubfeature.name }} subfeature?</v-card-text>
                <v-card-actions>
                <v-btn color="primary" text @click="dialogDelete = false">Close</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="red" text @click="deleteSubfeature()">Delete</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <!-- Subfeature information dialog -->
        <v-dialog v-model="dialogInfo" max-width="500px">
            <v-card class="subfeature-info">
                <v-card-title>Subfeature information</v-card-title>
                <v-card-text>
                    <dl class="row">
                        <dt class="col-3 text-end">Name:</dt>
                        <dd class="col-9">{{ selectedSubfeature.name }}</dd>
                    </dl>
                </v-card-text>
                <v-card-text>
                    <v-divider></v-divider>
                    <dl class="row">
                        <dt class="col-3 text-end">Created:</dt>
                        <dd class="col-9">{{ selectedSubfeature.created | formatDate }}</dd>
                        <dt class="col-3 text-end">Created By:</dt>
                        <dd class="col-9">{{ selectedSubfeature.created_by.fullname || selectedSubfeature.created_by.username}}</dd>
                        <template v-if="selectedSubfeature.updated_by">
                            <dt class="col-3 text-end">Updated:</dt>
                            <dd class="col-9">{{ selectedSubfeature.updated | formatDate }}</dd>
                            <dt class="col-3 text-end">Updated By:</dt>
                            <dd class="col-9">{{ selectedSubfeature.updated_by.fullname || selectedSubfeature.updated_by.username}}</dd>
                        </template>
                    </dl>
                </v-card-text>
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
                componentTab: null,

                // Dialogs
                dialog: false,
                dialogPlatforms: false,
                dialogDelete: false,
                dialogInfo: false,

                rules: {
                    required: value => !!value || 'Required.'
                },

                components: [],
                codecs: [],
                featureCategories: [],
                features: [],
                generations: [],
                platforms: [],
                platformsByGen: {},
                subFeatures: [],
                subFeaturesByComponent: [],

                selectedGenerations: [],
                selectedCodecs: [],
                selectedPlatforms: [],
                selectedOS: oses.WINDOWS_OS,
                editedIndex: -1,
                selectedSubfeature: {
                    'feature': {'name': undefined},
                    'win_platforms': [],
                    'lin_platforms': [],
                    'created_by': {'fullname': undefined},
                    'updated_by': {'fullname': undefined},
                },
                defaultSubfeature: {
                    'feature': {'name': undefined},
                    'win_platforms': [],
                    'lin_platforms': [],
                    'created_by': {'fullname': undefined},
                    'updated_by': {'fullname': undefined},
                },
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
            dialogInfo(val) {
                val || this.closeInfoDialog()
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
            getSubfeaturesByComponent(componentId) {
                this.subFeaturesByComponent = this.subFeatures.filter((sf) => sf.component.id == componentId)
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
                // Codecs filter
                // Subfeature that are not supported in the selected filters are not shown
                let showCodec = this._.includes(this.selectedCodecs, subfeature.codec.id)
                let showAllGens = this.selectedGenerations.length == this.generations.length &&
                    this.selectedPlatforms.length == this.platforms.length

                if (!showCodec) {
                    return false
                }
                else if (showAllGens) {
                    return true
                }
                let win_platforms = subfeature.win_platforms.filter((item) => this.selectedPlatforms.indexOf(item.id) >= 0)
                let lin_platforms = subfeature.lin_platforms.filter((item) => this.selectedPlatforms.indexOf(item.id) >= 0)
                return win_platforms.length || lin_platforms.length
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
                        this.getSubfeaturesByComponent(this.components[0].id)
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
                this.selectedSubfeature[this.platformKey(this.selectedOS)] = this.editedPlatforms
                this.dialogPlatforms = false
            },
            editPlatforms(os) {
                this.dialogPlatforms = !this.dialogPlatforms
                this.selectedOS = os
                this.editedPlatforms = this.selectedSubfeature[this.platformKey(os)]
            },
            editSubfeatures(item) {
                this.editedIndex = this.subFeatures.indexOf(item)
                this.selectedSubfeature = Object.assign({}, item)
                this.dialog = true
            },
            openDeleteDialog(item) {
                this.selectedSubfeature = Object.assign({}, item)
                this.dialogDelete = !this.dialogDelete
            },
            openInfoDialog(item) {
                this.selectedSubfeature = Object.assign({}, item)
                this.dialogInfo = !this.dialogInfo
            },
            deleteSubfeature() {
                server
                    .delete(`${url}${this.selectedSubfeature.id}/`)
                    .then(response => {
                        let index = this._.findIndex(this.subFeatures, {id: this.selectedSubfeature.id})
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
                    .finally(() => {
                        this.closeDeleteDialog()
                        this.getSubfeaturesByComponent(this.componentTab)
                    })
            },
            close() {
                this.dialog = false
                this.$nextTick(() => {
                    this.selectedSubfeature = Object.assign({}, this.defaultSubfeature)
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
                    this.selectedSubfeature = Object.assign({}, this.defaultSubfeature)
                })
            },
            closeInfoDialog() {
                this.dialogInfo = false
                this.$nextTick(() => {
                    this.selectedSubfeature = Object.assign({}, this.defaultSubfeature)
                })
            },
            save() {
                let sfSaving = {
                    name: this.selectedSubfeature.name,
                    component: this.selectedSubfeature.component.id,
                    codec: this.selectedSubfeature.codec.id,
                    category: this.selectedSubfeature.category.id,
                    feature: this.selectedSubfeature.feature.id,
                    lin_platforms: this.selectedSubfeature.lin_platforms.map((item) => item.id),
                    win_platforms: this.selectedSubfeature.win_platforms.map((item) => item.id)
                }

                if (this.editedIndex > -1) {
                    server
                        .put(`${url}${this.selectedSubfeature.id}/`, sfSaving)
                        .then(response => {
                            Object.assign(this.subFeatures[this.editedIndex], response.data)
                            this.$toasted.success('Subfeature has been edited')
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Error during requesting edition of this object', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                        .finally(() => {
                            this.close()
                            this.getSubfeaturesByComponent(this.componentTab)
                        })
                } else {
                    server
                        .post(this.url, sfSaving)
                        .then(response => {
                            this.selectedSubfeature.id = response.data.id
                            this.subFeatures.unshift(response.data)
                            this.$toasted.success('Subfeature has been created')
                        })
                        .catch(error => {
                            if (error.handleGlobally) {
                                error.handleGlobally('Error during requesting creation of a new object', url)
                            } else {
                                this.$toasted.global.alert_error(error)
                            }
                        })
                        .finally(() => {
                            this.close()
                            this.getSubfeaturesByComponent(this.componentTab)
                        })
                }
            },
        },
        created() {
            // Initial components, codecs, categories, features, platforms
            let url = 'api/component/'
            server
                .get(url)
                .then(response => {
                    this.components = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get components', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
            url = 'test_verifier/codecs/'
            server
                .get(url)
                .then(response => {
                    this.codecs = response.data
                    this.selectedCodecs = this.codecs.map((item) => item.id)
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
    .subfeatures .col-codec, .col-category, .col-feature {
        width: 170px;
    }
    .col-actions {
        width: 100px;
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
    .subfeature-info dt, .subfeature-info dd {
        padding-bottom: 0;
    }
    .subfeature-info dt {
        font-weight: 700;
    }
    .add-subfeature {
        position: absolute;
        right: 20px;
        top: 20px;
    }
</style>