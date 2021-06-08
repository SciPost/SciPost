import Vue from 'vue'
import VueCompositionAPI from '@vue/composition-api'
Vue.use(VueCompositionAPI)

import Search from './components/Search.vue'

new Vue({
    render: h => h(Search),
}).$mount('#search');
