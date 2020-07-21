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
            },
        },
    },
});
