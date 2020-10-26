import Vue from 'vue';

import vSelect from 'vue-select'

Vue.component('v-select', vSelect)

import 'vue-select/dist/vue-select.css';

import BootstrapVue from 'bootstrap-vue';
Vue.use(BootstrapVue);

//import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';


import VueSanitize from "vue-sanitize";
const sanitizationOptions = {
    allowedTags: [ // same as in markup.constants.py
	'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'em',
	'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'li', 'ol',
	'p', 'pre', 'strong', 'table', 'td', 'th', 'tr', 'ul'
    ],
    allowedAttributes: {
      'a': [ 'href' ]
    }
};
Vue.use(VueSanitize, sanitizationOptions);


import MessagesTable from './components/MessagesTable.vue'


new Vue({
    render: h => h(MessagesTable),
}).$mount('#messages-table');
