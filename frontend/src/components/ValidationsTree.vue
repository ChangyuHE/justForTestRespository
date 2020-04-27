<template>
    <v-jstree ref="tree"
        :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
    </v-jstree>
</template>
<script>
    import VJstree from 'vue-jstree';
    import server from '@/server.js';
    import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';

    function selectedValidationsText(branches) {
        // Get text for branch from list of components
        return branches.map(function(branch){
                let texted = branch.reverse().map((node) => (node.model.text));
                return `${texted[5]} (${texted[1]}, ${texted[3]}, ${texted[4]})`;
            }
        );
    }

    function getBranchForLeaf(node){
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

    export default {
        name: 'ValidationsTree',
        components: {
            VJstree
        },
        data() {
            return {
                data: null,
                loading: true,
                errored: false,
            }
        },
        methods: {
            itemClick(node) {
                let branches = [];
                let validations = [];
                let t = this.$refs.tree;

                t.handleRecursionNodeChilds(t,
                    node => {
                        if (typeof node.model!='undefined' && node.model.hasOwnProperty('selected') && node.model.selected && node.$children.length == 0) {
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
                        if (typeof node.model!='undefined' && node.model.hasOwnProperty('selected') && node.model.selected)
                            node.model.selected = false;
                    }
                )
                this.$store.commit('setSelected', { validations: [], branches: [] });
            },
        },
        beforeCreate() {
            // getting initial data
            server
                .get('api/validations/')
                .then(response => {
                    this.data = response.data;
                })
                .catch(error => {
                    console.log(error)
                    this.errored = true
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
</style>