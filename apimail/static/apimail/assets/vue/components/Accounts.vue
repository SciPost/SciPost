<template>
<div class="overflow-auto">
  <b-card bg-variant="light">
    <b-form-group>
      <div v-for="access in accesses">
	<input
	  type="radio"
	  v-model="accountSelected"
	  :id="access"
	  :value="access.account.email"
	  >
	{{ access.account.email }}
      </div>
      <!-- <b-form-checkbox-group -->
      <!-- 	v-model="accountSelected"> -->
      <!-- 	<b-form-checkbox v-for="account in accounts" :value="account.email"> -->
      <!-- 	  {{ account }} -->
      <!-- 	</b-form-checkbox> -->
      <!-- </b-form-checkbox-group> -->
    </b-form-group>
    <p>Account to display: {{ accountSelected }}</p>
  </b-card>
</div>
</template>

<script>
export default {
    name: "user-accounts-table",
    data() {
	return {
	    accesses: null,
	    accountSelected: null,
	}
    },
    methods: {
	fetchAccounts () {
	    fetch('/mail/api/user_account_accesses')
		.then(stream => stream.json())
		.then(data => this.accesses = data.results)
		.catch(error => console.error(error))
	}
    },
    mounted() {
	this.fetchAccounts()
    },
}
</script>
