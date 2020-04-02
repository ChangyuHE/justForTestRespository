<template>
    <v-app>
        <v-navigation-drawer v-model="drawer" app color="blue-grey lighten-5">
            <v-list dense>
                <v-list-item link>
                    <v-list-item-action>
                        <v-icon>mdi-home</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>Link 1</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
                <v-list-item link>
                    <v-list-item-action>
                        <v-icon>mdi-card-account-mail</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>Link 2</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>

        <v-app-bar app color="teal darken-1" dark short>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title>GRep tool</v-toolbar-title>
        </v-app-bar>

        <v-content>
            <v-overlay :value="treeLoading">
                <v-progress-circular indeterminate size="64"></v-progress-circular>
            </v-overlay>
            <v-container fluid>
                <v-row>
                    <v-col>
                        <v-jstree ref="tree"
                            :data="jstreeData" show-checkbox allow-batch multiple @item-click="itemClick">
                        </v-jstree>
                    </v-col>
                    <v-divider vertical></v-divider>
                    <v-col class="pa-6" cols="6">
                        <v-row justify="start" align="start">
                            <v-list dense flat>
                                <v-subheader>Selected Validations</v-subheader>
                                    <v-list-item v-for="(item, i) in selectedValidationsText" :key="i">
                                        <v-list-item-content>
                                            <v-list-item-title v-text="item"></v-list-item-title>
                                        </v-list-item-content>
                                    </v-list-item>
                            </v-list>
                        </v-row>
                        
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
    import VJstree from 'vue-jstree';
    import server from './server.js';

    /**
     *  returns list of nodes from leaf to root
     */
    function getBranchForLeaf(node){
        let branch = [node];
        if (node.$children.length == 0) {   // is leaf
            while (node.$parent.model !== undefined) {      // is root
                node = node.$parent;
                branch.push(node);
            }
        }
        return branch;
    }


	export default {
        components: {
            VJstree
        },
        data() {
            return {
                jstreeData: null,
                treeLoading: true,
                errored: false,
                drawer: false,
                selectedValidations: [],
                selectedBranches: []
            }
        },
		computed: {
            selectedValidationsText(){
                return this.selectedBranches.map(function(branch){
                        let texted = branch.reverse().map((node) => (node.model.text));
                        return `${texted[5]} (${texted[1]}, ${texted[3]}, ${texted[4]})`;
                    }
                );
            }
        },
        methods: {
            itemClick(node) {
                //console.log('node:', node);
                this.selectedBranches = [];
                this.selectedValidations = [];

                this.$refs.tree.handleRecursionNodeChilds(this.$refs.tree,
                    node => {
                        if (typeof node.model!='undefined' && node.model.hasOwnProperty('selected') && node.model.selected && node.$children.length == 0) {
                            this.selectedBranches.push(getBranchForLeaf(node));
                            this.selectedValidations.push(node.model.id);
                        }
                    }
                )
            }
        },
        beforeCreate() {
            server
                .get('api/validations/')
                .then(response => {
                    //console.log(response.data);
                    this.jstreeData = response.data;
                })
                .catch(error => {
                    console.log(error)
                    this.errored = true
                  })
                .finally(() => this.treeLoading = false)
        }
	}
</script>

<style>
    .i-windows {
        background: url(./assets/icons/windows.svg) !important;
    }
    .i-linux {
        background: url(./assets/icons/linux.svg) !important;
    }
    .i-platform {
        background: url(./assets/icons/chip.svg) !important;
    }
    .i-gen {
        background: url(./assets/icons/cpu.svg) !important;
    }
    .i-validation {
        background: url(./assets/icons/list.svg) !important;
    }
    .i-simulation {
        background: url(./assets/icons/simulation.svg) !important;
    }
    .icon-custom {
        width: 20px !important;
        height: 20px !important;
        margin: 2px !important;
        padding: 2px !important;
    }
</style>
