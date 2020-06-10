import Vue from 'vue'
import App from './App.vue'
import store from './store'
import router from './router'

import vuetify from './plugins/vuetify'
import vueDebounce from 'vue-debounce'
import VueToasted from 'vue-toasted'

Vue.use(VueToasted, {
  iconPack : 'material',
  duration: 2500,
  action : {
    text : 'close',
    onClick : (e, toastObject) => { toastObject.goAway(0)}
  }
});

// register custom toasts
Vue.toasted.register('alert_success',
  payload => payload, { type : 'success', icon : 'check', duration: null }
)

Vue.toasted.register('alert_error',
  payload => payload, { type : 'error', icon : 'warning', duration: null }
)

Vue.toasted.register('alert_error_detailed',
  ({header, message}) => {
    return `${header}<br>${message}`
  },
  { type : 'error', icon : 'warning', duration: null, closeOnSwipe: false,
    action: [
      {
        icon: 'assignment',
        onClick : (e, toastObject) => {
          let dummy = document.createElement('textarea');
          dummy.textContent = toastObject.el.textContent.slice(7, -15);
          document.body.appendChild(dummy);

          let selection = document.getSelection();
          let range = document.createRange();
          range.selectNode(dummy);
          selection.removeAllRanges();
          selection.addRange(range);
          document.execCommand('copy');
          selection.removeAllRanges();
          document.body.removeChild(dummy);

          alert("Error details copied to clipboard.");
        }
      },
      {
        text : 'close',
        onClick : (e, toastObject) => {
          toastObject.goAway(0);
        }
      }
    ]
  }
)

Vue.use(vueDebounce)
Vue.config.productionTip = false

new Vue({
  vuetify,
  store,
  router,
  render: h => h(App)
}).$mount('#app');

import 'material-icons/iconfont/material-icons.scss'