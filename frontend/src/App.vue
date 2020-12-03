<template>
    <v-app>
        <!-- Left side drawer -->
        <v-navigation-drawer
            app disable-resize-watcher disable-route-watcher temporary
            color="blue-grey lighten-5"
            width="10%"
            v-model="drawer"
        >
            <v-list-item class="my-1 font-weight-medium">
                Settings
            </v-list-item>
            <v-divider></v-divider>
            <v-list dense>
                <v-list-item link to='/master-data' @click="drawer = !drawer">
                    <v-list-item-action class="mr-2">
                        <v-icon small>mdi-sitemap</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>Master Data</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>

        <!-- Application bar on top -->
        <v-app-bar app color="teal darken-2 elevation-4" dark short>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title class="mr-2 pl-1">Reporter</v-toolbar-title>
            <!-- Navigation buttons -->
            <v-btn v-for="routeData in routeDataMap" :key="routeData.name"
                :to="{name: routeData.name}"
                :class="$route.name == routeData.name && 'v-btn--active'"
                text exact
                @click="passParamsToURL"
            >
                {{ routeData.show }}
            </v-btn>
            <v-spacer></v-spacer>

            <!-- Help icon -->
            <v-btn
                icon
                href="https://wiki.ith.intel.com/display/MediaSDK/Reporter"
                target="_blank"
                title="Wiki documentation"
            >
                <v-icon>mdi-help-circle-outline</v-icon>
            </v-btn>

            <!-- User button -->
            <v-btn
                text
                class="mr-n2 px-2"
                style="text-transform: none"
                @click="usedCardRequired = true"
            >
                <v-icon>mdi-badge-account-horizontal-outline</v-icon>
                <span class="ml-2">{{ userName }}</span>
            </v-btn>
            <user-card v-if="usedCardRequired" @close="usedCardRequired = false"></user-card>
        </v-app-bar>

        <v-main>
            <v-container fluid class="pt-1">
                <!-- Router views will appers here -->
                <router-view></router-view>
            </v-container>
        </v-main>

        <!-- Scrolling to top -->
        <v-btn
            v-scroll="onScroll" v-show="showScroll"
            fab fixed bottom right
            color="blue-grey lighten-4"
            @click="toTop"
        >
            <v-icon class="d-inline">mdi-apple-keyboard-control</v-icon>
        </v-btn>

        <!-- Universal confirmation dialog -->
        <confirmation ref="confirm"></confirmation>
    </v-app>
</template>

<script>
    import server from './server.js'
    import { Splitpanes, Pane } from 'splitpanes'
    import 'splitpanes/dist/splitpanes.css'
    import { alterHistory } from '@/utils/history-management.js'
    import userCard from '@/components/UserCard.vue'
    import confirmation from '@/components/TheConfirmationDialog.vue'

    import { mapState, mapGetters } from 'vuex'

    import snow from '@/utils/snow.js'
    import Chance from 'chance'

    const IDLE = 15000
    function snowing() {
        const chance = Chance()
        const now = new Date()
        // the closer to YYYY-12-31 the bigger chance to see snow on idle
        const lucky = chance.bool({ likelihood: Math.round((now.getDate() / 31 * 100)) })
        if (now.getMonth() == 11 && lucky) {
            console.log('Let it snow!')
            let timeoutId = null
            timeoutId = setTimeout(() => snow(true), IDLE)

            window.addEventListener('mousemove', function() {
                clearTimeout(timeoutId)
                snow(false)
                timeoutId = setTimeout(() => snow(true), IDLE)
            })
        }
    }

    export default {
        components: {
            userCard,
            confirmation
        },
        data() {
            return {
                drawer: false,
                userDialog: false,
                showScroll: false,
                usedCardRequired: false,
                routeDataMap: [
                    { name: 'home', show: 'Validations' },
                    { name: 'import', show: 'Import' },
                    { name: 'search', show: 'Search' },
                    { name: 'feature-mapping', show: 'Features' },
                    { name: 'test-verifier', show: 'Test Verifier' }
                ]
            }
        },
        computed: {
            ...mapState({rawUserData: 'userData', urlParams: 'urlParams'}),
            ...mapState('tree', ['validations']),
            ...mapState('reports', ['reportType']),
            ...mapGetters(['userName']),
            userData() {
                let data = {}
                for (let key in this.rawUserData) {
                    if (key != 'id')
                        data[key] = this.rawUserData[key]
                }
                return data
            }
        },
        methods: {
            passParamsToURL() {
                // only for click on Validations button
                if (this.$route.name == 'home') {
                    alterHistory('replace', this.urlParams)
                }
            },
            onScroll(e) {
                if (typeof window === 'undefined') return
                const top = window.pageYOffset || e.target.scrollTop || 0
                this.showScroll = top > 20
            },
            toTop() {
                this.$vuetify.goTo(0)
            },
        },
        created() {
            // "back" and "front" buttons in browser
            window.onpopstate = event => {
                let url = new URL(window.location)
                let currentPath = url.pathname

                if (currentPath == this.$route.path)
                    location.reload()
            }
        },
        mounted() {
           this.$root.$confirm = this.$refs.confirm.open

           snowing()
        }
    }
</script>

<style>
    /* .router-active, .router-active-exact {
        color: white !important;
        text-decoration: none !important;
    } */
    /* vue-toasted alert container */
    .toasted {
        font-size: 16px !important;
        padding: 14px !important;
        font-family: 'Roboto', sans-serif !important;
    }
    .toasted .action {
        color: white !important;
        font-size: 14px !important;
    }
    .toasted-container.top-right {
        right: 1% !important;
    }
    /* just edited "ok" animation */
    .selected-row-ok {
        animation: selected-row-ok 2s 1;
    }
    @keyframes selected-row-ok {
        from {background-color: rgba(166, 219, 206, 0.647)}
        to {background-color: rgba(255, 255, 255, 0)}
    }
    /* just edited "error" animation */
    .selected-row-error {
        animation: selected-row-error 2s 1;
    }
    @keyframes selected-row-error {
        from {background-color: rgba(255, 41, 41, 0.452)}
        to {background-color: rgba(255, 255, 255, 0)}
    }
    .horizontal-line {
        border-color: rgba(0, 0, 0, 0.3) !important;
    }
</style>
