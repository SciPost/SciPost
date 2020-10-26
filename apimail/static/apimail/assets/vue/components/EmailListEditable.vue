<template>
<div>
  <ul>
    <li
      is="email-list-item"
      v-for="(email, index) in emails"
      :key="keyword + '-' + index"
      :email="email"
      @remove="emails.splice(index, 1)"
      >
    </li>
  </ul>
  <!-- <form @submit.prevent="addEmail"> -->
  <!--   <input -->
  <!--     v-model="newEmail" -->
  <!--     placeholder="Add" -->
  <!--     type="email" -->
  <!--     > -->
  <!--   <button>Add</button> -->
  <!-- </form> -->
  <select-from-address-book @selected="addSelectedEmail"></select-from-address-book>
</div>
</template>

<script>

import EmailListItem from './EmailListItem.vue'
import SelectFromAddressBook from './SelectFromAddressBook.vue'

export default {
    name: "email-list-editable",
    components: {
	EmailListItem,
	SelectFromAddressBook
    },
    props: {
	keyword: {
	    type: String,
	    required: true,
	},
	emails: {
	    type: Array,
	    required: true,
	},
    },
    // data () {
    // 	return {
    // 	    newEmail: '',
    // 	}
    // },
    methods: {
	// addEmail () {
	//     this.emails.push(this.newEmail)
	//     this.newEmail = ''
	// },
	addSelectedEmail (value) {
	    this.emails.push(value.address)
	}
    }
}
</script>
