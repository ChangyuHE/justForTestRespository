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

        <v-app-bar app color="teal darken-1" dark>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title>GRep tool</v-toolbar-title>
        </v-app-bar>

        <v-content>
            <v-container fluid>
                <v-row align="center" justify="center">
                    <v-col>
                        <v-jstree
                            :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
                        </v-jstree>
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

	export default {
        components: {
            VJstree
        },
        data() {
            return {
                data: null,
                loading: true,
                errored: false,
                drawer: false,
            }
        },
		computed: {

        },
        methods: {
            itemClick(node) {
                //console.log(node.model.text + ' clicked !');
                console.log('node:', node);
            }
        },
        beforeCreate() {
            server
                .get('api/validations/')
                .then(response => {
                    console.log(response.data);
                    this.data = response.data;
                })
                .catch(error => {
                    console.log(error)
                    this.errored = true
                  })
                .finally(() => this.loading = false)
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
