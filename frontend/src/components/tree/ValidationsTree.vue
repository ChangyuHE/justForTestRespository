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
        <v-btn-toggle
            class="mt-2" v-model="showFilters"
        >
            <!-- Badge with filters amount -->
            <v-badge class="filter-badge" color="teal darken-3"
                :content="badgeFilterCount"
                :value="badgeFilterCount"
                overlap
            >
                <v-btn x-small color="blue-grey lighten-4" class="black--text">
                    Tree filters
                </v-btn>
            </v-badge>
        </v-btn-toggle>

        <!-- Show date filters button -->
        <v-btn-toggle
            class="mt-2 ml-2" background-color="blue-grey" color="blue-grey darken-4"
            v-model="showDateSlider"
        >
            <v-badge class="date-badge" color="teal darken-3"
                :value="enableDates"
                overlap
            >
                <v-btn x-small color="blue-grey lighten-4" class="black--text">
                    Date filter
                </v-btn>
            </v-badge>
        </v-btn-toggle>

        <!-- Filters card -->
        <v-card class="mt-3 mr-4 elevation-2" v-show="showFilters == 0">
            <v-row class="d-flex">
                <v-col cols="12" class="py-0 mx-0 px-0">
                    <!-- Validations searchbox -->
                    <v-text-field
                        v-debounce:500ms="doFilter"
                        v-model="valToSearch"
                        color="blue-grey" class="mx-3 my-3 px-4 pt-1 filter-validation"
                        clearable dense hide-details
                    >
                        <template v-slot:append-outer>
                            <v-tooltip bottom v-model="showTooltip">
                                <template v-slot:activator="{ on }">
                                    <v-icon size="20" @click="showTooltip = !showTooltip">mdi-help-circle</v-icon>
                                </template>
                                Search by substring occurance in <strong class="font-weight-bold body-1">Validation name</strong>. Case insensitive.
                            </v-tooltip>
                        </template>
                        <template v-slot:label>
                            <span class="blue-grey--text text--darken-2">Validation name template</span>
                        </template>
                    </v-text-field>
                </v-col>
                <!-- Selectors -->
                <v-col cols="6" class="py-0 mx-0 px-0" v-for="i in treeStructure" :key="i.name">
                    <v-select class="mx-3 my-2 px-4 pt-1 filter-select"
                        color="blue-grey"
                        item-color="blue-grey"
                        clear-icon="mdi-close"
                        return-object multiple clearable small-chips deletable-chips hide-details
                        :items="i.items"
                        @change="doSelection($event, i.level)"
                    >
                        <template v-slot:label>
                            <span class="blue-grey--text text--darken-2" v-text="i.label"></span>
                        </template>
                    </v-select>
                </v-col>
            </v-row>
        </v-card>

        <!-- Slider card -->
        <v-card class="mt-3 mr-4 elevation-2" min-width="510" v-show="showDateSlider == 0">
            <v-row class="">
                <v-col cols="12" class="pt-0 px-6 d-flex">
                    <!-- Date filtering switch -->
                    <v-switch
                        class="mt-1 d-flex align-self-center date-switch"
                        hide-details color="teal darken-1"
                        v-model="enableDates"
                    />
                    <!-- Display range -->
                    <span class="ml-1 mt-2 d-flex align-center">
                        Date range:
                        <template v-if="enableDates">
                            <span class="subtitle font-weight-bold ml-2 mr-1">{{ dateStart }}</span> &ndash;
                            <span class="subtitle font-weight-bold ml-1">{{ dateEnd }}</span>
                        </template>
                        <template v-else>
                            <span class="subtitle font-weight-bold ml-2 mr-1">All available</span>
                        </template>
                    </span>
                    <v-spacer></v-spacer>
                    <span class="mt-2 d-flex align-center" :class="{ disabled_text: !enableDates }">Last </span>
                    <!-- Pre-defined range buttons group -->
                    <v-btn-toggle
                        class="ml-2 mt-2" color="teal darken-1"
                        v-model="sliderButtonValue"
                        @change="sliderButtonClick"
                    >
                        <v-btn small v-for="b_item in sliderButtons" :key="b_item.months" :disabled="!enableDates">
                            {{ b_item.text }}
                        </v-btn>
                    </v-btn-toggle>
                </v-col>
                <!-- Slider -->
                <v-col cols="12" class="d-flex px-6 py-0">
                    <v-range-slider hide-details
                        step="1" max="11"
                        ticks tick-size="8" :tick-labels="ticksLabels"
                        class="mb-4" color="teal" track-color="teal lighten-4"
                        :disabled="!enableDates"
                        v-model="sliderValue"
                        @change="this.sliderButtonValue = undefined"
                    ></v-range-slider>
                </v-col>
            </v-row>
        </v-card>

        <!-- Derevo -->
        <v-jstree ref="tree" v-if="data.length" class="mt-4"
            :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
        </v-jstree>
        <v-card v-else outlined class="ml-4 mr-7 mt-4">
            <v-card-text class="text-center subtitle-1">No data to show</v-card-text>
        </v-card>
    </div>
</template>
<script>
    import qs from 'query-string'
    import VJstree from 'vue-jstree'
    import server from '@/server.js'
    import { mapState } from 'vuex'
    import { monthData, monthLabels, lastDaysData, maxMonthsShown } from './dates.js'
    import { replaceState, pushState } from '@/utils/history-management.js'

    // Get text for branch from list of components
    function selectedValidationsText(branches) {
        return branches.map(function(branch) {
                let texted = branch.reverse().map((node) => (node.model.text_flat))
                return `${texted[5]} (${texted[1]}, ${texted[3]}, ${texted[4]})`
            }
        )
    }

    // get branch as list of nodes for clicked node
    function getBranchForLeaf(node) {
        let branch = [node]
        if (node.$children.length == 0) {   // is leaf
            while (node.$parent.model !== undefined) {      // is root
                node = node.$parent
                branch.push(node)
            }
        }
        return branch
    }

    function getAvailableNodes(tree) {
        let nodes = []
        tree.handleRecursionNodeChilds(tree,
            node => {
                if (typeof node.model !='undefined' && node.$children.length == 0)
                    nodes.push(node)
            }
        )
        return nodes
    }
    // update tree data with selected validations data
    function setSelectedInData(searchObj, validations) {
        for (let prop in searchObj) {
            if (prop === 'id' && validations.includes(searchObj[prop])) {
                searchObj['selected'] = true
            } else if (typeof searchObj[prop] === 'object') {
                setSelectedInData(searchObj[prop], validations)
            }
        }
    }

    function highlightSearchData(searchObj, toSearch) {
        for (let prop in searchObj) {
            if (prop === 'level' && searchObj['level'] == 5) {
                searchObj['text'] = searchObj['text'].replace(new RegExp(toSearch, "gi"), (match) => `<span class="highlighted-text">${match}</span>`)
            } else if(typeof searchObj[prop] === 'object') {
                highlightSearchData(searchObj[prop], toSearch)
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
                // tree data
                data: [],

                // filtering
                selectedData: {},
                treeStructure: null,
                treeFilterLoading: false,
                showFilters: undefined,
                badgeFilterCount: 0,
                valToSearch: '',
                showTooltip: false,

                // date slider
                enableDates: false,
                showDateSlider: undefined,
                sliderValue: [6, 11],
                ticksLabels: monthLabels,
                sliderButtons: [
                    {'months': 0, 'text': '1 m'},
                    {'months': 2, 'text': '3 m'},
                    {'months': 5, 'text': '6 m'},
                    {'months': 11, 'text': '1 y'},
                ],
                sliderButtonValue: null,
                initiallyLoaded: false,
            }
        },
        computed: {
            ...mapState('tree', ['treeLoading', 'validations']),
            dateStart() {
                return monthData[this.sliderValue[0]] + '-1'
            },
            dateEnd() {
                return monthData[this.sliderValue[1]] + '-' + lastDaysData[this.sliderValue[1]]
            }
        },
        watch: {
            valToSearch() {
                if (!this.valToSearch && this.badgeFilterCount > 0) {
                    this.badgeFilterCount--
                    this.doFilter()
                }
            },
            sliderValue() {
                this.doFilter()
            },
            enableDates() {
                this.doFilter()
            },
            validations(value) {
                if (!value.length)
                    this.clear()
            }
        },
        methods: {
            // set range according to clicked group button
            sliderButtonClick() {
                if (this.sliderButtonValue !== undefined) {
                    let rangeL = this.sliderButtons[this.sliderButtonValue]['months']
                    let start = maxMonthsShown-1-rangeL
                    start = start > 0 ? start: 0
                    this.sliderValue = [start, maxMonthsShown-1]
                }
            },
            doSelection(selected, level) {
                this.selectedData[level] = selected
                if (!selected.length)
                    delete this.selectedData[level]
                this.doFilter()
            },
            /**
             * Combine data from fitering components, send request to back,
             * then update tree data, set checked status for validations in tree, highlight if needed
             */
            doFilter() {
                let data = []
                this.badgeFilterCount = 0
                if (this.valToSearch)
                    this.badgeFilterCount++

                this.treeFilterLoading = true

                for (let [k, v] of Object.entries(this.selectedData)) {
                    data.push({'level': +k, 'text': v})
                    this.badgeFilterCount += v.length
                }
                if (this.valToSearch) {
                    data.push({'level': 5, 'text': this.valToSearch})
                }
                if (this.enableDates) {
                    data.push({'start': new Date(this.dateStart).toISOString(), 'end': new Date(this.dateEnd).toISOString()})
                }

                const url = `api/validations/?data=${encodeURIComponent(JSON.stringify(data))}`
                server
                    .get(url)
                    .then(response => {
                        this.data = response.data

                        // set checked status for already selected validations in tree
                        if (this.validations.length)
                            setSelectedInData(this.data, this.validations)

                        // highlight matched part in validation names
                        if (this.valToSearch)
                            highlightSearchData(this.data, this.valToSearch)
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Failed to get filtered validations', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.treeFilterLoading = false)
            },
            /**
             * On tree item click fill "validations" and "branches" store variables
             */
            itemClick(node) {
                let branches = []
                let validations = []

                // if filter is active then select available nodes ..
                if (this.badgeFilterCount > 0 || this.enableDates) {
                    if (node.model.selected == false) {
                        let branches = []
                        let validations = []

                        getAvailableNodes(this.$refs.tree).forEach(node => {
                            branches.push(getBranchForLeaf(node))
                            validations.push(node.model.id)
                        })
                        // .. and delete them from selection
                        this.$store.dispatch('tree/removeFiltered', { validations, branches: selectedValidationsText(branches) })
                    }
                }
                // select all checked nodes
                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model !='undefined' && node.model.selected && node.$children.length == 0) {
                            branches.push(getBranchForLeaf(node))
                            validations.push(node.model.id)
                        }
                    }
                )

                // if filter is active add selected
                if (this.badgeFilterCount > 0 || this.enableDates) {
                    this.$store.dispatch('tree/addSelected', { validations, branches: selectedValidationsText(branches) })
                // if not just set selected
                } else {
                    this.$store.dispatch('tree/setSelected', { validations, branches: selectedValidationsText(branches) })
                }

                // add selected validations to url query
                pushState({selected: this.validations})
            },
            /**
             * Uncheck all validations and clear url query
             */
            clear() {
                if (this.$refs.tree !== undefined) {
                    this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                        node => {
                            if (typeof node.model != 'undefined' && node.model.selected)
                                node.model.selected = false
                        }
                    )
                    // delete all query params
                    history.replaceState(null, null, this.$route.path)
                }
            },
            IDsToSelection() {
                let branches = []
                let validations = []
                if (this.$refs.tree !== undefined) {
                    this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                        node => {
                            if (typeof node.model != 'undefined' && node.model.selected) {
                                branches.push(getBranchForLeaf(node))
                                validations.push(node.model.id)
                            }
                        }
                    )
                    this.$store
                        .dispatch('tree/setSelected', { validations, branches: selectedValidationsText(branches) })
                }
            }
        },
        beforeCreate() {
            // Initial tree data
            let url = 'api/validations/'
            this.$store.dispatch('tree/setTreeLoading', true)
            server
                .get(url)
                .then(response => {
                    this.data = response.data

                    // parse router query for selected validations or get from store ..
                    if (this.$route.query.selected || this.validations.length) {
                        let selectedIds = []
                        if (this.validations.length) {      // went form other views (already have values in store)
                            selectedIds = this.validations
                        } else {                            // or following direct link
                            selectedIds = this.$route.query.selected.split(',')
                        }

                        function getObject(array, key, value) {
                            let obj
                            array.some(function iter(child) {
                                if (child[key] == value && child.klass == 'Validation') {
                                    obj = child
                                    return true
                                }
                                return Array.isArray(child.children) && child.children.some(iter)
                            })
                            return obj
                        }
                        // .. and update tree data with selected ids
                        selectedIds.forEach(id => {
                            let nodeData = getObject(this.data, 'id', id)
                            nodeData.selected = true
                        })
                    }
                    this.initiallyLoaded = true
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get initial validations tree data', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })

            // Variants of nodes values for filters
            url = 'api/validations/structure'
            server
                .get(url)
                .then(response => {
                    this.treeStructure = response.data
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get validations tree available node data', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
                .finally(() => this.$store.dispatch('tree/setTreeLoading', false))
        },
        updated() {
            this.initiallyLoaded && this.IDsToSelection()
        }
    }
</script>
<style>
    /* Tree icons */
    .i-windows {
        background: url(../../assets/icons/windows.svg) !important;
    }
    .i-linux {
        background: url(../../assets/icons/linux.svg) !important;
    }
    .i-platform {
        background: url(../../assets/icons/chip.svg) !important;
    }
    .i-gen {
        background: url(../../assets/icons/cpu.svg) !important;
    }
    .i-validation {
        background: url(../../assets/icons/list.svg) !important;
    }
    .i-simulation {
        background: url(../../assets/icons/simulation.svg) !important;
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
    /* smaller close icon */
    .filter-select .mdi-close, .filter-validation .mdi-close {
        font-size: 20px !important;
    }
    .filter-validation .mdi-help-circle {
        top: 2px !important;
    }
    /* badges near filtering buttons */
    .filter-badge .v-badge__badge, .date-badge .v-badge__badge {
        padding: 2px !important;
        height: 14px !important;
        min-width: 14px !important;
        font-size: 9px !important;
        left: calc(100% - 7px) !important;
        top: -4px !important;
    }
    .v-slider__tick {
        background-color: #80CBC4 !important;
        border-radius: 12px !important;
        border: solid 2px white !important;
    }
    .v-input--selection-controls__ripple {
        height: 24px !important;
        width: 24px !important;
        margin: 12px !important;
    }
    .disabled_text {
        color: #a7a7a7;
    }
    .v-slider__tick-label {
        font-size: 80% !important;
    }
    .v-slider__thumb-container:hover .v-slider__thumb:before {
        transform: scale(1.5) !important;
    }
    .v-slider__thumb:before {
        width: 20px !important;
        height: 20px !important;
        left: -4px !important;
        top: -4px !important;
    }
    .highlighted-text {
        color: #E64A19;
    }
</style>