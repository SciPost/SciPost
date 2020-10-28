<template>
<div>
  <v-select
    v-model="selected"
    :options="addressOptions"
    @search="onSearchAddressBook"
    placeholder="Type to search in your address book"
    label="address"
    :filterable="false"
    >
    <template v-slot:no-options="{ search, searching }">
      <template v-if="searching">
	<span class="bg-danger px-4 py-2 text-white">No match found in your address book</span>
      </template>
      <template v-else>
	Type to search in your address book
      </template>
    </template>
    <template slot="option" slot-scope="option">
      {{ option.address }}
      <span v-if="option.description"><br>&emsp;<em>({{ option.description }})</em></span>
    </template>
    <template slot="selected-option" slot-scope="option">
      {{ option.address }}
    </template>
    <template #spinner="{ loading }">
      <div v-if="loading" style="border-left-color: rgba(88,151,251,0.71)" class="vs__spinner">
      </div>
    </template>
  </v-select>
</div>
</template>

<script>
var debounce = require('lodash.debounce');

export default {
    name: "select-from-address-book",
    data () {
	return {
	    selected: null,
	    addressOptions: [],
	}
    },
    methods: {
	onSearchAddressBook (search, loading) {
	    loading(true)
	    this.searchAddressBook(loading, search, this)
	},
	searchAddressBook: debounce((loading, search, vm) => {
	    fetch(
		`/mail/api/address_book/select?q=${escape(search)}`
	    ).then(res => {
		res.json().then(json => (vm.addressOptions = json.results))
		loading(false);
	    });
	}, 350),
    },
    watch: {
	selected: function () {
	    this.$emit('selected', this.selected)
	    this.selected = null
	}
    }
}
</script>
