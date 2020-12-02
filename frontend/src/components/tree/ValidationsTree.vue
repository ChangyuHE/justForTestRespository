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

        <v-row>
            <div class="d-flex-inline">
                <!-- Show filters button -->
                <v-btn-toggle
                    class="mt-2 ml-3"
                    v-model="showFilters"
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
                    class="mt-2 ml-2"
                    background-color="blue-grey" color="blue-grey darken-4"
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

                <!-- Help icon -->
                <v-btn
                    icon
                    small
                    href="https://wiki.ith.intel.com/display/MediaSDK/List+of+available+validations"
                    target="_blank"
                    title="Validations list documentation"
                >
                    <v-icon size="20">mdi-help-circle-outline</v-icon>
                </v-btn>
            </div>

            <v-spacer></v-spacer>
            <!-- Clean and actions buttons -->
            <div>
                <div style="position: fixed; margin-left: -295px; z-index: 1">
                    <div class="d-flex justify-end">
                        <!-- Validations actions show/hide button -->
                        <v-btn
                            text x-small
                            class="mt-2 mx-1 px-0"
                            @click="showValActions = !showValActions"
                            :class="{'primary--text text--darken-1': showValActions}"
                        >
                            <v-icon>mdi-dots-horizontal</v-icon>
                        </v-btn>
                        <!-- Clear tree filters -->
                        <v-btn x-small color="blue-grey lighten-4" class="mr-1 mt-2"
                            :disabled="disableClearFilters"
                            @click="clearFilters"
                        >
                            clear filters
                        </v-btn>
                        <!-- Clear selected validations -->
                        <v-btn x-small color="blue-grey lighten-4" class="mt-2"
                            :disabled="!validations.length"
                            @click="clearValidations"
                        >
                            <v-badge
                                class="clear-button-badge" color="teal darken-3"
                                :content="validations.length"
                                :value="validations.length"
                                overlap
                            >
                                clear selection
                            </v-badge>
                        </v-btn>
                    </div>
                    <!-- UNCOMMENT WHEN REQUIRED -->
                    <!-- Validations actions buttons -->
                    <div class="mt-2 d-flex justify-end">
                        <template v-if="showValActions">
                            <v-btn
                                x-small
                                color="blue-grey lighten-4"
                                class="ml-1"
                                :disabled="!badgeFilterCount && !enableDates"
                                @click="userFiltersDialog = true"
                            >
                                Save filters
                            </v-btn>
                            <v-btn
                                x-small
                                color="blue-grey lighten-4"
                                class="ml-1"
                            :disabled="!(validations.length && validations.length > 1 && selectedNodesInOneBranch)"
                            v-show="showValActions"
                            @click="showMergeDialog = true"
                            >
                                Merge
                            </v-btn>
                            <v-btn
                                x-small
                                color="blue-grey lighten-4"
                                class="ml-1"
                                :disabled="!(validations.length && validations.length == 1)"
                                v-show="showValActions"
                                @click="showCloneDialog = true"
                            >
                                Clone
                            </v-btn>
                            <!-- <v-btn
                                x-small
                                color="blue-grey lighten-4"
                                class="ml-1"
                                :disabled="!(validations.length && validations.length == 1)"
                                v-show="showValActions"
                            >
                                Lock
                            </v-btn> -->
                        </template>
                    </div>
                </div>
            </div>
        </v-row>

        <!-- Filters card -->
        <v-card class="mt-3 mr-4 pr-4 pb-2 elevation-2" v-show="showFilters == 0">
            <v-row class="d-flex">
                <v-col cols="6" class="py-0">
                    <!-- Validations searchbox -->
                    <v-text-field
                        v-debounce:500ms="filterByValidation"
                        v-model="selectors.validation"
                        color="blue-grey" class="ml-4 my-3 pt-1 filter-validation"
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
                <v-col cols="6" class="py-0 d-flex">
                    <!-- Users filter -->
                    <v-autocomplete class="mx-2 my-2 pt-1 px-2 filter-select"
                        color="blue-grey"
                        item-color="blue-grey"
                        clear-icon="mdi-close"
                        item-text="name"
                        multiple clearable small-chips deletable-chips hide-details return-object
                        :menu-props="{closeOnContentClick: true}"
                        :items="usersData"
                        v-model="selectors.user"
                        @change="filterBySelector($event, 'user')"
                    >
                        <template v-slot:label>
                            <span class="blue-grey--text text--darken-2">User</span>
                        </template>
                    </v-autocomplete>
                    <v-btn-toggle
                        class="align-center" color="teal darken-1"
                        v-model="showMyValidations"
                        @change="filterMyValidations"
                    >
                        <v-btn :value="true" x-small>my</v-btn>
                    </v-btn-toggle>
                </v-col>
                <!-- Selectors -->
                <v-col
                    v-for="selector in treeStructure" :key="selector.name"
                    cols="6" class="py-0"
                >
                    <v-autocomplete class="ml-4 my-2 pt-1 filter-select"
                        color="blue-grey"
                        item-color="blue-grey"
                        clear-icon="mdi-close"
                        :item-text="filterItemText(selector.level)"
                        return-object multiple clearable small-chips deletable-chips hide-details
                        :menu-props="{closeOnContentClick: true}"
                        :items="selector.items"
                        v-model="selectors[selector.level]"
                        @change="filterBySelector($event, selector.level)"
                    >
                        <template v-slot:label>
                            <span class="blue-grey--text text--darken-2" v-text="selector.label"></span>
                        </template>
                    </v-autocomplete>
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
                        @change="setDateRange"
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
                        @change="sliderButtonValue = undefined"
                    ></v-range-slider>
                </v-col>
            </v-row>
        </v-card>

        <!-- Derevo -->
        <v-jstree ref="tree" v-if="data.length" class="mt-4"
            :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
            <template slot-scope="_">
                <div style="display: inherit;" @click.exact="itemClick(_.vm, _.model, $event)">
                <i :class="_.vm.themeIconClasses" role="presentation" v-if="!_.model.loading"></i>
                    <span v-html="_.model.text"></span>
                    <template v-if="_.model.level == 'validation'">
                        <span v-if="hasAnyStatus(_.model)"> &mdash; </span>
                        <template v-for="status in ['passed', 'failed', 'error', 'blocked', 'skipped', 'canceled']">
                            <span v-if="_.model[status] != 0"
                                :key="status"
                                class="mr-1"
                                :class="getStatusColor(status)"
                                :title="status"
                            >
                                <small>{{ _.model[status] }}</small>
                            </span>
                        </template>
                        <!-- Validation params -->
                        <i
                            title="Validation properties"
                            class="v-icon mdi mdi-text-box-outline theme--light validation-action-icon"
                            @click.stop="editValidation(_.model.id)"
                        ></i>
                        <!-- Validation actions -->
                        <i
                            title="Delete validation"
                            v-if="_.model.owner == userData.id"
                            class="v-icon mdi mdi-delete theme--light validation-action-icon delete"
                            @click.stop="deleteValidation(_.model)"
                        ></i>
                    </template>
                </div>
            </template>
        </v-jstree>
        <v-card v-else flat class="ml-4 mr-7 mt-4">
            <v-card-text class="text-center text-h6 grey--text">No data to show</v-card-text>
        </v-card>

        <validation-clone-dialog
            v-if="showCloneDialog"
            :selected-node="selectedNode"
            @close="showCloneDialog = false"
        ></validation-clone-dialog>

        <validation-merge-dialog
            v-if="showMergeDialog"
            :selected-nodes="selectedNodes"
            @close="showMergeDialog = false"
        ></validation-merge-dialog>

        <!-- Save filters to profile as user default -->
        <filters-save-dialog
            v-if="userFiltersDialog"
            :selectors="selectors"
            :dates="{enabled: enableDates, sliderRange: sliderValue, sliderButton: sliderButtonValue}"
            @close="userFiltersDialog = false"
        ></filters-save-dialog>

        <validation-edit-dialog
            v-if="editValidationDialog"
            :node="editedNode"
            :tree-structure="treeStructure"
            @close="editValidationDialog = false"
        ></validation-edit-dialog>
    </div>
</template>
<script>
    import { mapState, mapGetters } from 'vuex'
    import { EventBus } from '@/event-bus.js'

    import qs from 'query-string'
    import server from '@/server.js'
    import { monthLabels, lastDaysData, maxMonthsShown, sliderButtons, dateStart, dateEnd } from './dates.js'
    import { alterHistory } from '@/utils/history-management.js'
    import { getTextColorFromStatus } from '@/utils/styling.js'
    import rules from '@/utils/form-rules.js'
    import { isIDsFilter, filterItemText, getBranchForLeaf } from './common.js'

    import VJstree from 'vue-jstree'
    import FiltersSaveDialog from './TheFiltersSaveDialog.vue'
    import ValidationEditDialog from './TheValidationEditDialog.vue'
    import ValidationCloneDialog from './TheValidationCloneDialog.vue'
    import ValidationMergeDialog from './TheValidationMergeDialog.vue'

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
            if (prop === 'level' && searchObj['level'] == 'validation') {
                searchObj['text'] = searchObj['text'].replace(new RegExp(toSearch, "gi"), (match) => `<span class="highlighted-text">${match}</span>`)
            } else if(typeof searchObj[prop] === 'object') {
                highlightSearchData(searchObj[prop], toSearch)
            }
        }
    }

    // push Filters params to url or delete if empty
    function addFiltersToUrl(value, level) {
        let key = `treeFilter-${level}`
        if (isIDsFilter(level)) {
            if (value === null || !value.length) {
                alterHistory('push', {}, [key])
            } else if (value.length) {
                alterHistory('push', {[key]: value.map(e => e.id)})
            }
        } else {
            if (value) {
                alterHistory('push', {[key]: value})
            } else {
                alterHistory('push', {}, [key])
            }
        }
    }

    export default {
        name: 'ValidationsTree',
        components: {
            VJstree,
            ValidationCloneDialog,
            ValidationMergeDialog,
            FiltersSaveDialog,
            ValidationEditDialog
        },
        data() {
            return {
                // tree data
                data: [],

                // filtering
                selectors: {validation: '', user: [], gen: [], os: [], os_group: [], platform: [], component: [], feature: []},
                showMyValidations: undefined,

                treeStructure: null,
                treeFilterLoading: false,
                showFilters: undefined,
                badgeFilterCount: 0,
                showTooltip: false,
                showValActions: false,
                usersData: [],
                showCloneDialog: false,
                showMergeDialog: false,
                userIdToName: {},

                // date slider
                enableDates: false,
                showDateSlider: undefined,
                sliderValue: [6, 11],
                ticksLabels: monthLabels,
                sliderButtons: sliderButtons,
                sliderButtonValue: null,

                userFiltersDialog: false,
                editValidationDialog: false,
                editedNode: undefined,
            }
        },
        computed: {
            ...mapState(['userData']),
            ...mapState('tree', ['treeLoading', 'validations']),
            dateStart() {
                return dateStart(this.sliderValue[0])
            },
            dateEnd() {
                return dateEnd(this.sliderValue[1])
            },
            disableClearFilters() {
                return !this.enableDates && this._.every(this._.values(this.selectors), this._.isEmpty)
            },
            // first of selected nodes
            selectedNode() {
                return this.selectedNodes.length ? this.selectedNodes[0] : null
            },
            selectedNodes() {
                let selectedNodes = []
                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                        node => {
                            if (typeof node.model != 'undefined' && !node.$children.length && this.validations.includes(node.model.id)) {
                                selectedNodes.push(node)
                            }
                        }
                )
                return selectedNodes
            },
            selectedNodesInOneBranch() {
                if (!this.selectedNodes.length) return false

                // make array of unique values from array of childs of all selected nodes
                let allChilds = this._.flatten(this.selectedNodes.map(node => node.$parent.$children))
                return this._.uniq(allChilds).length === this.selectedNodes[0].$parent.$children.length
            }
        },
        watch: {
            /**
             * watch for validation filter change to null
             * required due to debounce in text field is not fired in case of field clear by cross click)
             */
            'selectors.validation': function(value) {
                if (!value && this.badgeFilterCount > 0) {
                    this.badgeFilterCount--
                    addFiltersToUrl(this.selectors.validation, 'validation')
                    this.doFilter()
                }
            },
            'selectors.user': function(value) {
                if (!this._.isEmpty(value)) {
                    if (this._.map(value, 'id').includes(this.userData.id)) {
                        this.showMyValidations = true
                    } else {
                        this.showMyValidations = undefined
                    }
                } else {
                    this.showMyValidations = undefined
                }
            },
            sliderValue() {
                this.doFilter()
            },
            enableDates() {
                this.doFilter()
            },
            validations(value) {
                // clear selected param in url and checkboxes in tree
                if (!value.length) {
                    this.clearTree()
                }
            },
            sliderButtonValue(value) {
                if (value === undefined) {
                    alterHistory('push', {}, ['treeDates-button'])
                }
            }
        },
        methods: {
            filterItemText(model) {
                return filterItemText(model)
            },
            filterMyValidations(value) {
                if (value) {
                    this.selectors.user.unshift(this.usersData.find(e => e.id == this.userData.id))
                } else {
                    this.selectors.user = this.selectors.user.filter(e => this.userData.id !== e.id)
                }
                addFiltersToUrl(this.selectors.user, 'user')
                this.doFilter()
            },
            // set range according to clicked group button
            setDateRange() {
                if (this.sliderButtonValue !== undefined) {
                    let rangeL = this.sliderButtons[this.sliderButtonValue]['months']
                    let start = maxMonthsShown-1-rangeL
                    start = start > 0 ? start: 0
                    this.sliderValue = [start, maxMonthsShown-1]
                } else {
                    alterHistory('push', {}, ['treeDates-button'])
                }
            },
            filterBySelector(selected, level) {
                addFiltersToUrl(selected, level)
                this.doFilter()
            },
            filterByValidation() {
                addFiltersToUrl(this.selectors.validation, 'validation')
                this.doFilter()
            },
            // push Dates params to url
            addDatesToUrl(sliderValues, buttonValue) {
                let params = {}
                let toDelete = []

                this._.each({'range': sliderValues, 'button': buttonValue}, (value, key) => {
                    key = `treeDates-${key}`
                    if (typeof value == 'number') {
                        params[key] = value.toString()
                    } else {
                        if (this._.isEmpty(value)) {
                            toDelete.push(key)
                        } else if (value.length) {
                            params[key] = this._.map(value, this._.toString)
                        }
                    }
                })
                alterHistory('push', params, toDelete)
            },
            /**
             * Combine data from fitering components, pass params to URL, send request to back,
             * then update tree data, set checked status for validations in tree, highlight if needed
             */
            doFilter() {
                this.treeFilterLoading = true
                let data = []
                this.badgeFilterCount = 0

                // fill Filters data to send
                for (let [k, v] of Object.entries(this.selectors)) {
                    if (!this._.isEmpty(v)) {
                        if (isIDsFilter(k)) {
                            data.push({'level': k, 'value': this._.map(v, 'id')})
                            this.badgeFilterCount += v.length
                        } else {
                            data.push({'level': k, 'value': v})
                            this.badgeFilterCount++
                        }
                    }
                }
                // Dates management
                if (this.enableDates) {
                    this.addDatesToUrl(this.sliderValue, this.sliderButtonValue)
                    let start = new Date(this.dateStart).toISOString()
                    let end = new Date(this.dateEnd).toISOString()
                    data.push({start, end})
                } else {
                    this.addDatesToUrl(null, null)
                }

                const url = `api/validations/?data=${encodeURIComponent(JSON.stringify(data))}`
                server
                    .get(url)
                    .then(response => {
                        this.data = response.data

                        // set checked status for already selected validations in tree
                        if (this.validations.length) {
                            setSelectedInData(this.data, this.validations)
                        }
                        // highlight matched part in validation names
                        if (this.selectors.validation) {
                            highlightSearchData(this.data, this.selectors.validation)
                        }
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
                let getBranchLeafs = node => {
                    let validations = []
                    let branches = []

                    function isLeafOfBranch(branchRoot, node) {
                        while (node.$parent.model !== undefined) {
                            if (node.$parent._uid == branchRoot._uid) {
                                return true
                            }
                            node = node.$parent
                        }
                        return false
                    }
                    this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                        n => {
                            if (typeof n.model && n.$children.length == 0 && isLeafOfBranch(node, n)) {
                                branches.push(getBranchForLeaf(n))
                                validations.push(n.model.id)
                            }
                        }
                    )
                    return [validations, branches]
                }
                let branches = []
                let validations = []

                // Fill selected validations ids and branches with preserved order
                if (node.$children.length) {
                    // branch
                    [validations, branches] = getBranchLeafs(node)
                } else {
                    validations = [node.model.id]
                    branches = [getBranchForLeaf(node)]
                }

                if (node.model.selected) {
                    this.$store.dispatch('tree/addSelected', { validations, branches: this.prepareBranches(branches) })
                } else {
                    this.$store.dispatch('tree/removeSelected', { validations, branches: this.prepareBranches(branches) })
                }

                // add selected validations to url query
                alterHistory('push', {selected: this.validations})
            },
            prepareBranches(branches) {
                let result = []
                for (const branch of branches) {
                    let levelResult = []
                    for (const level of branch) {
                        if (level.model.level != 'validation') {
                            levelResult.push(level.model.text_flat)
                        } else {
                            levelResult.push(
                                {
                                    'text': level.model.text_flat,
                                    'owner': this.userIdToName[level.model.owner],
                                    'date': level.model.date,
                                    'passed': level.model.passed,
                                    'failed': level.model.failed,
                                    'error': level.model.error,
                                    'blocked': level.model.blocked,
                                    'skipped': level.model.skipped,
                                    'canceled': level.model.canceled,
                                }
                            )
                        }
                    }
                    levelResult.reverse()
                    result.push(levelResult)
                }
                return result
            },
            /**
             * Get params from URL and set validations and branches
             */
            validationsAndBranchestoStore() {
                // parse URL
                let parsed = qs.parse(location.search, { arrayFormat: 'comma' })
                if (this._.isEmpty(parsed)) {
                    return
                }
                let validations = []

                // get validations parameter from parsed
                if (typeof parsed.selected == 'object') {
                    validations = this._.map(parsed.selected, this._.toNumber)
                } else if (parsed.selected) {
                    validations = [+parsed.selected]
                }
                let branches = Array(validations.length)

                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model != 'undefined' && node.model.selected && !node.$children.length && validations.includes(node.model.id)) {
                            let index = validations.indexOf(node.model.id)
                            if (index !== -1) {
                                branches.splice(index, 1, getBranchForLeaf(node))
                            }
                        }
                    }
                )
                if (validations.length) {
                    this.$store.dispatch('tree/setSelected', { validations, branches: this.prepareBranches(branches) })
                }
            },
            /**
             * Get filtering params from URL and apply to tree
             */
            applyUrlFilterParams() {
                let parsed = qs.parse(location.search, {arrayFormat: 'comma'})

                this._.each(parsed, (value, key) => {
                    if (key.includes('treeFilter')) {
                        this.showFilters = 0
                        this.fillSelector(key.split('-')[1], value)
                    } else if (key.includes('treeDates')) {
                        this.showDateSlider = 0
                        this.enableDates = true
                        this.fillDate(key.split('-')[1], value)
                    }
                })
                if (this.showFilters !== undefined || this.showDateSlider !== undefined) {
                    this.doFilter()
                }
                this.$store.dispatch('setUrlParams', qs.parse(location.search, { arrayFormat: 'comma' }))
            },
            fillSelector(level, value) {
                if (isIDsFilter(level)) {
                    let selectedIds
                    if (typeof value == 'object') {
                        selectedIds = this._.values(value)
                    } else {
                        selectedIds = [value]
                    }
                    selectedIds = this._.map(selectedIds, this._.toNumber)
                    // get available objects for our level
                    let levelObjects
                    if (level !== 'user') {
                        levelObjects = this.treeStructure.find(e => e.level == level).items
                    } else {
                        levelObjects = this.usersData
                    }
                    // filter them by selected ids
                    this.selectors[level] = levelObjects.filter(e => selectedIds.includes(e.id))
                } else {
                    this.selectors[level] = value
                }
            },
            fillDate(key, value) {
                if (this._.isEmpty(value)) {
                    return
                }
                if (key == 'range') {
                    this.sliderValue = this._.map(value, this._.toNumber)
                } else if (key == 'button') {
                    this.sliderButtonValue = +value
                }
            },
            /**
             * Clear methods
             */
            // Uncheck all validations in tree and update url query
            clearTree() {
                if (this.$refs.tree !== undefined) {
                    this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                        node => {
                            if (typeof node.model != 'undefined' && node.model.selected) {
                                node.model.selected = false
                            }
                        }
                    )
                    alterHistory('push', {}, ['selected'])
                }
            },
            // Set no validations and branches in store
            clearValidations() {
                this.$store.dispatch('tree/setSelected', { validations: [], branches: [] })
            },
            // Wipe out all filters
            clearFilters() {
                // date
                this.enableDates = false
                this.sliderButtonValue = null
                this.sliderValue = [6, 11]
                // tree
                this.selectors = {validation: '', user: [], gen: [], os: [], os_group: [], platform: [], component: [], feature: []}
                // close panels
                this.showFilters = undefined
                this.showDateSlider = undefined
                // clear URL params
                alterHistory(
                    'push',
                    {},
                    ['treeDates-button', 'treeDates-range',
                     'treeFilter-gen', 'treeFilter-os', 'treeFilter-os_group',
                     'treeFilter-platform', 'treeFilter-validation',
                     'treeFilter-user', 'treeFilter-component', 'treeFilter-feature']
                )
            },
            getStatusColor(status) {
                return getTextColorFromStatus(status)
            },
            hasAnyStatus(el) {
                return this._.some([el.passed, el.failed, el.error, el.blocked, el.skipped, el.canceled], function(e) { return e != 0 })
            },
            updateStatusCounters(oldStatuses, newStatus, validation_id) {
                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model != 'undefined' && node.model.selected && !node.$children.length && node.model.id === validation_id) {
                            for (const [status, number] of Object.entries(oldStatuses)) {
                                if (number != 0) {
                                    node.model[status.toLowerCase()] -= number
                                }
                            }
                            for (const [status, number] of Object.entries(newStatus)) {
                                node.model[status.toLowerCase()] += number
                            }
                        }
                    }
                )
            },
            editValidation(id) {
                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model != 'undefined' && !node.$children.length && node.model.id == id) {
                            this.editedNode = node
                        }
                    }
                )
                this.editValidationDialog = true
            },
            async deleteValidation(model) {
                if (
                    await this.$root.$confirm(
                        'Delete validation',
                        `Are you sure you want to delete "${model.name}" validation?`,
                        { color: 'red' }
                    )
                ) {
                    const url = `/api/validations/update/${model.id}/`
                    server
                        .delete(url)
                        .then(response => {
                            // remove from selected validations/braches
                            alterHistory('replace', { selected: this._.without(this.validations, model.id) })
                            // update validations and branches
                            this.validationsAndBranchestoStore()
                            // set url params to store
                            this.$store.dispatch('setUrlParams', qs.parse(location.search, {arrayFormat: 'comma'}))
                            window.location.reload()

                            this.$toasted.success('Successfully deleted')
                        })
                        .catch(error => {
                            error.handleGlobally && error.handleGlobally('Could not delete validation', url)
                        })
                }
            },
            initialTreeLoad() {
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

                            // get validation object by "item[key] == value" condition from tree data structure
                            function getObject(array, key, value) {
                                let obj
                                // 'some' is used just to iterate over array and call 'iterate' function for each item
                                array.some(
                                    // recursively iterate over 'children' array of input child object
                                    function iterate(child) {
                                        if (child[key] == value && child.klass == 'Validation') {
                                            obj = child
                                            return true
                                        }
                                        return Array.isArray(child.children) && child.children.some(iterate)
                                    }
                                )
                                return obj
                            }
                            // update tree data with selected ids
                            selectedIds.forEach(id => {
                                let nodeData = getObject(this.data, 'id', id)
                                if (nodeData !== undefined) {
                                    nodeData.selected = true
                                } else {
                                    // no such validation in tree - remove from url
                                    alterHistory('replace', { selected: this._.without(selectedIds, id) })
                                }
                            })
                        }
                        this.$nextTick(() => {
                            this.validationsAndBranchestoStore()
                            this.applyUrlFilterParams()
                            // set url params to store
                            this.$store.dispatch('setUrlParams', qs.parse(location.search, { arrayFormat: 'comma' }))
                        })
                    })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally('Failed to get initial validations tree data', url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    })
                    .finally(() => this.$store.dispatch('tree/setTreeLoading', false))
            }
        },
        beforeCreate() {
            // Get users with validations
            let url = 'api/users/?validations=true'
            server
                .get(url)
                .then(response => {
                    this.usersData = response.data
                    // create value to show in dropdown
                    this._.map(this.usersData, e => {
                        e.name = `${e.first_name} ${e.last_name} (${e.username})`
                    })
                    // create mapping user id -> user name
                    for (const user of this.usersData) {
                        this.userIdToName[user.id] = user.name
                    }
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get users data for filter', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })

            // Variants of filters dropdowns
            url = 'api/validations/structure'
            server
                .get(url)
                .then(response => {
                    this.treeStructure = response.data
                    return server.get('api/component/?active=True')
                })
                .then(response => {
                    this.treeStructure.push({items: response.data, label: 'Component', level: 'component'})
                    return server.get('api/result_feature/?active=True')
                })
                .then(response => {
                    this.treeStructure.push({items: response.data, label: 'Feature', level: 'feature'})
                })
                .catch(error => {
                    if (error.handleGlobally) {
                        error.handleGlobally('Failed to get validations tree filters available items', url)
                    } else {
                        this.$toasted.global.alert_error(error)
                    }
                })
                .finally(() => {
                    this.initialTreeLoad()
                })
        },
        mounted() {
            EventBus.$on('update-counters', payload => {
                this.updateStatusCounters(payload.old, payload.new, payload.validation)
            })
        }
    }
</script>
<style>
    /* move checked checkbox 1px upper */
    .tree-default.tree-checkbox-selection .tree-selected>.tree-checkbox, .tree-default .tree-checked>.tree-checkbox {
        background-position: -228px -5px !important;
    }
    /* move empty checkbox 1px upper */
    .tree-default .tree-checkbox {
        background-position: -164px -5px !important;
    }
    /* rippple animation for tree row */
    .tree-anchor {
        background-position: center !important;
        transition: background 0.5s !important;
    }
    .tree-anchor:hover {
        background: #c6e6e3 radial-gradient(circle, transparent 1%, #c6e6e3 1%) center/15000% !important;
    }
    .tree-anchor:active {
        background-color: #72c9c0 !important;
        background-size: 100% !important;
        transition: background 0s !important;
    }
    /* background of selected tree node */
    .tree-selected {
        background-color: #bfd4dd75 !important;
    }
    /* custom tree-icon customization */
    .tree-icon {
        font-size: 24px;
        color: #234c61;
    }
    /* shrink tree row for 1 px */
    .tree-default .tree-anchor {
        line-height: 23px !important;
        height: 23px !important;
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

<style scoped>
    .validation-action-icon {
        font-size: 16px;
        color: #E0E0E0;
    }
    .validation-action-icon:hover {
        color: #00796B;
    }
    .validation-action-icon.delete:hover {
        color: #D32F2F;
    }
</style>
