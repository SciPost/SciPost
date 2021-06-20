import Vue from 'vue';

// import BootstrapVue from 'bootstrap-vue';
// Vue.use(BootstrapVue);


import {
    // Layout
    BRow, BCol,
    // Badges
    BBadge,
    // Buttons
    BButton, BButtonGroup, BButtonToolbar,
    // Cards
    CardPlugin,
    // Collapse
    BCollapse,
    // Forms
    FormPlugin, FormCheckboxPlugin, BFormFile, BFormGroup, BFormInput, FormRadioPlugin, BFormSelect,
    // Input
    BInputGroup, BInputGroupAppend,
    // Modal
    ModalPlugin,
    // Pagination,
    BPagination,
    // Spinner
    BSpinner,
    // Tabs
    TabsPlugin,
    // Tables
    TablePlugin,
    // Toggle
    VBToggle,
    // Tooltips
    VBTooltip,
} from 'bootstrap-vue';

// Cards
Vue.use(CardPlugin)
// Collapse
Vue.component('b-collapse', BCollapse)
// Forms
Vue.use(FormPlugin)
Vue.use(FormCheckboxPlugin)
Vue.component('b-form-file', BFormFile)
Vue.component('b-form-group', BFormGroup)
Vue.component('b-form-input', BFormInput)
Vue.use(FormRadioPlugin)
Vue.component('b-form-select', BFormSelect)
// Input
Vue.component('b-input-group', BInputGroup)
Vue.component('b-input-group-append', BInputGroupAppend)
// Pagination
Vue.component('b-pagination', BPagination)
// Tables
Vue.use(TablePlugin)
// Tabs
Vue.use(TabsPlugin)


// Style
//import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';


import vSelect from 'vue-select'
Vue.component('v-select', vSelect)
import 'vue-select/dist/vue-select.css';


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
