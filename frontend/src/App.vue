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
        <v-app-bar app color="teal darken-2 elevation-4" dark short>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title class="mr-2">Reporter</v-toolbar-title>
            <v-btn v-for="rItem in routeMap" :key="rItem.name" :to="{name: rItem.name}" text exact>
                {{ rItem.show }}
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn icon>
                <v-icon title="Account placeholder">mdi-account</v-icon>
            </v-btn>
        </v-app-bar>

        <v-content>
            <v-container fluid class="pt-0">
                <!-- Router views will appers here -->
                <router-view></router-view>
            </v-container>
        </v-content>
        <v-footer app class="justify-end">
            <span >&copy; 2020</span>
        </v-footer>
    </v-app>
</template>

<script>
    import server from './server.js'
    import validationsTree from './components/ValidationsTree'
    import alert from './components/Alert'
    import { Splitpanes, Pane } from 'splitpanes'
    import 'splitpanes/dist/splitpanes.css'

	export default {
        data() {
            return {
                drawer: false,
                routeMap: [
                    { name: 'home', show: 'Validations' },
                    { name: 'import', show: 'Import' }
                ]
            }
        }
	}
</script>

<style>
    /* .router-active, .router-active-exact {
        color: white !important;
        text-decoration: none !important;
    } */
</style>
