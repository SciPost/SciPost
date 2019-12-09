import Vue from 'vue';

import BootstrapVue from 'bootstrap-vue';
Vue.use(BootstrapVue);

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';


import MessageHeaderListItem from './components/MessageHeaderListItem.vue'
Vue.component('message-header-list-item', MessageHeaderListItem);


var messageList = new Vue({
    el: '#message-header-list',
    data: {
	apidata: [],
	results: [],
    },
    created: function () {
	fetch('/mail/api/stored_messages')
	    .then(stream => stream.json())
	    .then(data => this.apidata = data)
	    .catch(error => console.error(error))
    }
})
