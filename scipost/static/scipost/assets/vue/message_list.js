import Vue from 'vue';

import BootstrapVue from 'bootstrap-vue';
Vue.use(BootstrapVue);

// import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';


import MessageHeaderList from './components/MessageHeaderList.vue'

new Vue({
    render: h => h(MessageHeaderList),
}).$mount('#message-header-list');
