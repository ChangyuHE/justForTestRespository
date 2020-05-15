<template>
    <div>
        <!-- Grey loading overlay -->
        <v-overlay :value="treeLoading">
            <v-progress-circular indeterminate size="64"></v-progress-circular>
        </v-overlay>
        <!-- Tree filterign overlay -->
        <v-overlay :value="treeFilterLoading" absolute opacity="0.25">
            <v-progress-circular indeterminate size="64"></v-progress-circular>
        </v-overlay>

        <!-- Show filters button -->
        <v-btn-toggle class="mt-2" background-color="blue-grey" color="blue-grey darken-4">
            <!-- Badge with filters amount -->
            <v-badge class="filter-badge" color="teal darken-2"
                :content="badgeCount"
                :value="badgeCount"
                overlap
            >
                <v-btn x-small @click="showFilters = !showFilters" style="color: black;" class="elevation-2">
                    Tree filters
                </v-btn>
            </v-badge>
        </v-btn-toggle>

        <!-- Filters card -->
        <v-card class="mt-3 mr-4 elevation-2" v-show="showFilters">
            <v-row class="d-flex">
                <v-col cols="12" class="py-0 mx-0 px-0">
                    <!-- Validations searchbox -->
                    <v-text-field
                        v-debounce:500ms="doFilter"
                        v-model="valToSearch"
                        color="teal" class="mx-3 my-3 px-4 pt-1 filter-validation"
                        label="Validation name template"
                        clearable dense hide-details
                    >
                        <template v-slot:append-outer>
                            <v-tooltip bottom v-model="showTooltip" class="" style="">
                                <template v-slot:activator="{ on }">
                                    <v-icon size="20" style="" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                                </template>
                                Search by substring occurance in <strong class="font-weight-bold body-1">Validation name</strong>. Case insensitive.
                            </v-tooltip>
                        </template>
                    </v-text-field>
                </v-col>
                <!-- Selectors -->
                <v-col cols="6" class="py-0 mx-0 px-0" v-for="i in treeStructure" :key="i.name">
                    <v-select class="mx-3 my-3 px-4 pt-1 filter-select"
                        :items="i.items"
                        :label="i.label"
                        @change="doSelection($event, i.level)"
                        clear-icon="mdi-close" color="teal" item-color="teal darken-2"
                        multiple clearable dense small-chips return-object deletable-chips hide-details
                    ></v-select>
                </v-col>
            </v-row>
        </v-card>

        <v-jstree ref="tree" v-if="data.length" class="mt-4"
            :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
        </v-jstree>
        <v-card v-else outlined class="ml-4 mr-7 mt-4">
            <v-card-text class="text-center subtitle-1">No data to show</v-card-text>
        </v-card>
    </div>
</template>
<script>
    import VJstree from 'vue-jstree';
    import server from '@/server.js';
    import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';

    function selectedValidationsText(branches) {
        // Get text for branch from list of components
        return branches.map(function(branch) {
                let texted = branch.reverse().map((node) => (node.model.text_flat));
                return `${texted[5]} (${texted[1]}, ${texted[3]}, ${texted[4]})`;
            }
        );
    }

    function getBranchForLeaf(node) {
        // get branch as list of nodes for clicked node
        let branch = [node];
        if (node.$children.length == 0) {   // is leaf
            while (node.$parent.model !== undefined) {      // is root
                node = node.$parent;
                branch.push(node);
            }
        }
        return branch;
    }

    function setSelectedInData(searchObj, validations) {
        for (let prop in searchObj) {
            if (prop === 'id' && validations.includes(searchObj[prop])) {
                searchObj['selected'] = true;
            } else if (typeof searchObj[prop] === 'object') {
                setSelectedInData(searchObj[prop], validations);
            }
        }
    }

    function highlightSearchData(searchObj, toSearch) {
        for (let prop in searchObj) {
            if (prop === 'level' && searchObj['level'] == 5) {
                searchObj['text'] = searchObj['text'].replace(new RegExp(toSearch, "gi"), (match) => `<span style="color: #E64A19">${match}</span>`);
            } else if(typeof searchObj[prop] === 'object') {
                highlightSearchData(searchObj[prop], toSearch);
            }
        }
    }

    export default {
        name: 'ValidationsTree',
        components: {
            VJstree
        },
        data() {
            return {
                data: [],

                // filtering
                treeStructure: null,
                selectedData: {},
                treeFilterLoading: false,
                showFilters: false,
                badgeCount: 0,
                valToSearch: '',
                showTooltip: false,
            }
        },
        computed: {
            ...mapState(['treeLoading', 'validations']),
        },
        watch: {
            valToSearch() {
                if (!this.valToSearch && this.badgeCount > 0) {
                    this.badgeCount--;
                    this.doFilter()
                }
            }
        },
        methods: {
            doSelection(selected, level) {
                this.selectedData[level] = selected;
                if (!selected.length)
                    delete this.selectedData[level]
                this.doFilter()
            },
            /**
             * Combine data from fitering components, send request to back,
             * then update tree data, set checked status for validations in tree, highlight if needed
             */
            doFilter() {
                let data = [];
                this.badgeCount = 0;
                if (this.valToSearch)
                    this.badgeCount++;

                this.treeFilterLoading = true;

                for (let [k, v] of Object.entries(this.selectedData)) {
                    data.push({'level': +k, 'text': v})
                    this.badgeCount += v.length
                };
                if (this.valToSearch) {
                    data.push({'level': 5, 'text': this.valToSearch})
                }
                const url = `api/validations/?data=${encodeURIComponent(JSON.stringify(data))}`
                server
                    .get(url)
                    .then(response => {
                        this.data = response.data;

                        // set checked status for already selected validations in tree
                        if (this.validations.length)
                            setSelectedInData(this.data, this.validations);

                        // highlight matched part in validation names
                        if (this.valToSearch)
                            highlightSearchData(this.data, this.valToSearch);
                    })
                    .catch(error => {
                        console.log(error)
                        this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                        })
                    .finally(() => this.treeFilterLoading = false)
            },
            /**
             * On tree item click fill "validations" and "branches" store variables
             */
            itemClick(node) {
                let branches = [];
                let validations = [];

                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model !='undefined' && node.model.selected && node.$children.length == 0) {
                            branches.push(getBranchForLeaf(node));
                            validations.push(node.model.id);
                        }
                    }
                )
                this.$store.commit('setSelected', { validations, branches: selectedValidationsText(branches) });
            },
            clearValidations() {
                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model!='undefined' && node.model.selected)
                            node.model.selected = false;
                    }
                )
                this.$store.commit('setSelected', { validations: [], branches: [] });
            },
        },
        beforeCreate() {
            // Initial tree data
            let url = 'api/validations/';
            this.$store.commit('setTreeLoading', true);
            server
                .get(url)
                .then(response => {
                    this.data = response.data;
                })
                .catch(error => {
                    console.log(error)
                    this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                    })
                .finally()

            // Variants of nodes values for filters
            url = 'api/validations/structure';
            server
                .get(url)
                .then(response => {
                    this.treeStructure = response.data;
                })
                .catch(error => {
                    console.log(error);
                    this.$store.commit("setAlert", { message: `${error}<br> URL: ${server.defaults.baseURL}/${url}`, type: "error" });
                    })
                .finally(() => this.$store.commit('setTreeLoading', false))
        }
    }
</script>
<style>
    /* Tree icons */
    .i-windows {
        background: url(../assets/icons/windows.svg) !important;
    }
    .i-linux {
        background: url(../assets/icons/linux.svg) !important;
    }
    .i-platform {
        background: url(../assets/icons/chip.svg) !important;
    }
    .i-gen {
        background: url(../assets/icons/cpu.svg) !important;
    }
    .i-validation {
        background: url(../assets/icons/list.svg) !important;
    }
    .i-simulation {
        background: url(../assets/icons/simulation.svg) !important;
    }
    .icon-custom {
        width: 20px !important;
        height: 20px !important;
        margin: 2px !important;
        padding: 2px !important;
    }
    /* dense tree */
    .v-application ul, .v-application ol {
        padding-left: 0px !important;
    }
    .filter-select .mdi-close, .filter-validation .mdi-close {
        font-size: 20px !important;
    }
    .filter-validation .mdi-help-circle {
        top: 2px !important;
    }
    .filter-badge .v-badge__badge {
        padding: 3px 4px !important;
        height: 16px !important;
        font-size: 10px !important;
        min-width: 16px !important;
        left: calc(100% - 8px) !important;
    }
</style>