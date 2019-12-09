import Vue from 'vue';
import BootstrapVue from 'bootstrap-vue';

Vue.use(BootstrapVue);

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';

import MessageHeaderList from '../vue/components/MessageHeaderList.vue';

export default {
    components: {
	MessageHeaderList,
    },
}

window.Vue = Vue;
