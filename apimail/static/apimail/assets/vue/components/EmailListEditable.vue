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
  <form @submit.prevent="addEmail">
    <input
      v-model="newEmail"
      placeholder="Add"
      type="email"
      >
    <button>Add</button>
  </form>
</div>
</template>

<script>

import EmailListItem from './EmailListItem.vue'

export default {
    name: "email-list-editable",
    components: {
	EmailListItem,
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
    data () {
	return {
	    newEmail: '',
	}
    },
    methods: {
	addEmail () {
	    this.emails.push(this.newEmail)
	    this.newEmail = ''
	}
    }
}
</script>
