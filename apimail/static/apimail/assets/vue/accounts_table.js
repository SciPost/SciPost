import Vue from 'vue';

import BootstrapVue from 'bootstrap-vue';
Vue.use(BootstrapVue);

import 'bootstrap-vue/dist/bootstrap-vue.css';

import UserAccountsTable from './components/Accounts.vue'


new Vue({
    render: h => h(UserAccountsTable),
}).$mount('#user-accounts-table');
