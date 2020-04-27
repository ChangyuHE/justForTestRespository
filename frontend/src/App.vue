<template>
    <v-app>
        <!-- Left side drawer -->
        <v-navigation-drawer v-model="drawer" app color="blue-grey lighten-5">
            <v-list dense>
                <v-list-item link>
                    <v-list-item-action>
                        <v-icon>mdi-home</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>Placeholder 1</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
                <v-list-item link>
                    <v-list-item-action>
                        <v-icon>mdi-card-account-mail</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>Placeholder 2</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>

        <!-- Application bar on top -->
        <v-app-bar app color="teal darken-1" dark short>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title>GRep tool</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn icon>
                <v-icon title="Account placeholder">mdi-account</v-icon>
            </v-btn>
        </v-app-bar>

        <v-content>
            <!-- Grey loading overlay -->
            <v-overlay :value="treeLoading">
                <v-progress-circular indeterminate size="64"></v-progress-circular>
            </v-overlay>

            <v-container fluid class="pt-0">
                <v-row>
                    <v-col class="pt-2">
                        <splitpanes class="default-theme" ref="split" @pane-maximize="showExpand = true" @resize="showExpand = false">
                            <!-- Left part -->
                            <pane size="40" max-size="50">
                                <div class="d-flex">
                                    <!-- ">" button to show double-clicked pane -->
                                    <v-btn v-if="showExpand"
                                        fab x-small absolute fixed class="mt-2"
                                        color="blue-grey lighten-4"
                                        @click="expandPane"
                                    >
                                        <v-icon>mdi-chevron-right</v-icon>
                                    </v-btn>
                                    <!-- Validations tree -->
                                    <v-card width="100%" class="elevation-0 mt-4" color="transparent">
                                        <validations-tree ref="validations-tree" style="" class=""/>
                                    </v-card>
                                    <!-- Clear selection button -->
                                    <div class="d-flex justify-end">
                                        <v-btn x-small fixed color="blue-grey lighten-4" class="mx-n4 mt-4"
                                            :disabled="!validations.length"
                                            @click="clearSelected"
                                        >
                                            clear selection
                                        </v-btn>
                                    </div>
                                </div>
                            </pane>
                            <!-- Right part -->
                            <pane>
                                <div class="ml-4 mr-1 mt-2">
                                <!-- Buttons toolbar -->
                                <v-toolbar tile class="elevation-3">
                                    <!-- Best report button -->
                                    <v-btn small outlined color="teal darken-1"
                                        :disabled="!validations.length"
                                        :loading="bestLoading"
                                        @click="bestReportWeb"
                                    >Best results report</v-btn>
                                    <!-- Clear report -->
                                    <v-btn small outlined color="grey darken-1" class="mx-2"
                                        :disabled="!showBestTable"
                                        @click="showBestTable=false"
                                    >
                                        Clear
                                    </v-btn>
                                </v-toolbar>

                                <!-- Results card -->
                                <v-card class="my-4 elevation-3" v-if="showBestTable">
                                    <v-card-title class="mb-n4 ml-4">
                                        Best result for validations:
                                        <v-spacer></v-spacer>
                                        <!-- Search field -->
                                        <v-text-field
                                            v-model="search"
                                            append-icon="mdi-magnify"
                                            label="Search"
                                            hide-details
                                            class="pt-0 mt-0"
                                        ></v-text-field>

                                        <v-btn light small fab class="ml-4 elevation-5" @click="bestReportExcel">
                                            <v-icon>$excel</v-icon>
                                        </v-btn>
                                    </v-card-title>

                                    <!-- Validations list -->
                                    <v-list dense flat class="ml-4 mt-2">
                                        <v-list-item v-for="(item, i) in branches" :key="i">
                                            <v-list-item-content class="py-0 my-1">
                                                <v-list-item-title v-text="item"></v-list-item-title>
                                            </v-list-item-content>
                                        </v-list-item>
                                    </v-list>
                                    <v-divider style="border-color: rgba(0, 0, 0, 0.3); height:2px;"></v-divider>

                                    <!-- DataTable -->
                                    <v-data-table
                                        :headers="headers"
                                        :items="items"
                                        :search="search"
                                        :loading="bestTableLoading"
                                        disable-pagination hide-default-footer multi-sort
                                    >
                                        <template v-slot:item.passrate="{ item }">
                                            <v-chip :color="getColor(item.passrate)" light label>{{ item.passrate }}</v-chip>
                                        </template>
                                    </v-data-table>
                                </v-card>

                                <!-- Selected validations -->
                                <template v-if="!showBestTable && validations.length">
                                    <v-subheader class="mt-4" style="height: 32px;">
                                        Selected Validations
                                    </v-subheader>
                                    <v-list dense flat subheader class="ml-4" >
                                        <v-list-item v-for="(item, i) in branches" :key="i">
                                            <v-list-item-content class="py-0 my-1">
                                                <v-list-item-title v-text="item"></v-list-item-title>
                                            </v-list-item-content>
                                        </v-list-item>
                                    </v-list>
                                </template>

                                <!-- Scrolling to top -->
                                <v-btn
                                    v-scroll="onScroll" v-show="showScroll"
                                    fab fixed bottom right
                                    color="blue-grey lighten-4"
                                    @click="toTop"
                                >
                                    <v-icon class="d-inline">mdi-apple-keyboard-control</v-icon>
                                </v-btn>
                                </div>
                            </pane>
                        </splitpanes>
                    </v-col>
                </v-row>
            </v-container>
        </v-content>
        <v-footer app class="justify-end">
            <span >&copy; 2020</span>
        </v-footer>
    </v-app>
</template>

<script>
    import server from './server.js';
    import validationsTree from './components/ValidationsTree';
    import { Splitpanes, Pane } from 'splitpanes'
    import 'splitpanes/dist/splitpanes.css'

    import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';

	export default {
        components: {
            validationsTree,
            Splitpanes, Pane
        },
        data() {
            return {
                drawer: false,
                showScroll: false,      // "^" button
                showExpand: false,      // ">" button

                errored: false,

                // best report
                bestLoading: false,
                bestTableLoading: false,
                showBestTable: false,
                headers: [],
                items: [],
                search: '',
            }
        },
		computed: {
            ...mapState(['validations', 'branches', 'treeLoading']),
        },
        watch: {
            validations() {
                this.showBestTable = false;
            }
        },
        methods: {
            expandPane() {
                this.$refs['split'].panes[0].size = 50;
                this.showExpand = false;
            },
            clearSelected() {
                // direct call method from referenced component
                this.$refs['validations-tree'].clearValidations();
            },
            bestReportExcel() {
                /**
                 * Download Excel report generated on back based on selected validations ids
                 */
                let ids = this.validations.join(',');
                this.bestTableLoading = true;
                server
                    .get(`api/report/best/${ids}?report=excel`, {responseType: 'blob'})
                    .then(response => {
                        let fileName = 'unknown';
                        const contentDisposition = response.headers['content-disposition'];
                        if (contentDisposition) {
                            const m = contentDisposition.match(/filename="(.+)"/);
                            if (m.length == 2)
                                fileName = m[1];
                        }
                        const url = window.URL.createObjectURL(new Blob([response.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', fileName);
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    })
                    .catch(error => {
                        console.log(error)
                        this.errored = true
                    })
                    .finally(() => this.bestTableLoading = false);
            },
            bestReportWeb() {
                /**
                 * Get report data from backend based on selected validations ids
                 */
                let ids = this.validations.join(',');
                this.bestLoading = true;
                server
                    .get(`api/report/best/${ids}`).
                    then(response => {
                        // console.log(response.data);
                        this.headers = response.data.headers;
                        this.items = response.data.items;
                    })
                    .catch(error => {
                        console.log(error)
                        this.errored = true
                    })
                    .finally(() => {
                        this.bestLoading = false;
                        this.showBestTable = true;
                    });
            },
            onScroll(e) {
                if (typeof window === 'undefined') return;
                const top = window.pageYOffset || e.target.scrollTop || 0;
                this.showScroll = top > 20;
            },
            toTop() {
                this.$vuetify.goTo(0);
            },
            getColor(p) {
                /**
                 * Coloring passaretes in report
                 */
                p = Number(p.slice(0, -1));
                if (p >= 0 && p < 50) return 'red lighten-3'
                else if (p >= 50 && p < 80) return 'yellow lighten-4'
                else if (p >= 80 && p < 100) return 'green lighten-4'
                else return 'green lighten-1'
            },
        },
        // mounted() {
        //     this.showExpand = this.$refs['split'].panes[0].size == 0;
        // }
	}
</script>

<style>
    /* DataTable colored zebra */
    tbody tr:nth-of-type(odd) {
        background-color: rgba(0, 142, 100, .03);
    }
    /* DataTable header font */
    .v-data-table thead th {
        font-size: 14px !important;        
    }
    .v-list-item--dense, .v-list--dense .v-list-item {
        min-height: 20px !important;
    }
    /* Panes splitting */
    .splitpanes__pane {
        background-color: #FFFFFF !important;
    }
    .splitpanes__splitter {
        background-color: #ECEFF1 !important;
        box-shadow: 0px 3px 3px -2px rgba(0, 0, 0, 0.2), 0px 3px 4px 0px rgba(0, 0, 0, 0.34), 0px 1px 8px 0px rgba(0, 0, 0, 0.12) !important;
    }    
</style>
