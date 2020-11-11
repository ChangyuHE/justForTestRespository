import Vue from 'vue'
import Vuetify from 'vuetify/lib'
import '@mdi/font/css/materialdesignicons.css'

import excelIcon from '@/components/icons/excel.vue'

Vue.use(Vuetify);

export default new Vuetify({
    icons: {
        values: {
            excel: {    // name of our custom icon
                component: excelIcon,
            },
        },
    },
    theme: {
        themes: {
            light: {
                primary: '#009688',
                secondary: '#b0bec5',
                accent: '#A7FFEB',
                error: '#b71c1c',

                failed_status: '#C62828',       // red darken-3
                passed_status: '#43A047',       // green darken-1
                error_status: '#8E24AA',        // purple darken-1
                blocked_status: '#F9A825',      // yellow darken-3
                skipped_status: '#757575',      // grey darken-1
                canceled_status: '#90CAF9',     // blue lighten-3
            },
        },
    },
});
