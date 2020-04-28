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
});
