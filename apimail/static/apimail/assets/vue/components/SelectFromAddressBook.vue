<template>
<div>
  <v-select
    v-model="selected"
    :options="addressOptions"
    @search="onSearchAddressBook"
    label="address"
    >
    <template slot="no-options">
      Type to search your address book
    </template>
    <template slot="option" slot-scope="option">
      {{ option.address }}
      <span v-if="option.description"><br>&emsp;<em>({{ option.description }})</em></span>
    </template>
    <template slot="selected-option" slot-scope="option">
      {{ option.address }}
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
