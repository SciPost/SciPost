<template>
<div>

  <h2>Click on an account to view messages</h2>

  <table class="table">
    <tr>
      <th>Account</th>
      <th>Address</th>
      <th>Rights</th>
      <th>From</th>
      <th>Until</th>
    </tr>
    <tr
      v-for="access in accesses"
      v-bind:class="{'highlight': isSelected(access.account.email)}"
      v-on:click="accountSelected = access.account.email"
      v-on:change=""
      class="p-2 m-0"
      >
      <td>{{ access.account.name }}</td>
      <td>{{ access.account.email }}</td>
      <td>{{ access.rights }}</td>
      <td>{{ access.date_from }}</td>
      <td>{{ access.date_until }}</td>
    </tr>
  </table>

  <div v-if="accountSelected" :key="accountSelected">
    <b-card bg-variant="light">
      <b-row>
	<b-col class="col-lg-6">
	  <h2>Messages for <strong>{{ accountSelected }}</strong></h2>
	</b-col>
	<b-col class="col-lg-2">
	  <b-badge variant="primary">{{ totalRows }} total</b-badge>
	</b-col>
	<b-col class="col-lg-4">
	  <b-pagination
	    v-model="currentPage"
	    :total-rows="totalRows"
	    :per-page="perPage"
	    class="m-1"
	    align="center"
	    aria-controls="my-table"
	    >
	  </b-pagination>
	</b-col>
      </b-row>
      <hr>
      <b-row class="mb-0">
	<b-col class="col-lg-7">
	  <b-form-group
	    label="Filter:"
	    label-cols-sm="3"
            label-align-sm="right"
            label-size="sm"
	    >
	    <b-input-group size="sm">
	      <b-form-input
		v-model="filter"
		type="search"
		id="filterInput"
		placeholder="Type to search"
		>
	      </b-form-input>
	      <b-input-group-append>
		<b-button :disabled="!filter" @click="filter = ''">Clear</b-button>
	      </b-input-group-append>
	    </b-input-group>
	  </b-form-group>
	  <b-form-group
	    label="Time period:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    class="mb-0"
	    >
	    <b-form-radio-group
	      v-model="timePeriod"
	      :options="timePeriodOptions"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-5 mb-0">
	  <b-form-group
            label="Filter on:"
	    label-cols-sm="3"
            label-align-sm="right"
            label-size="sm"
            description="Leave all unchecked to filter on all data"
	    class="mb-0"
	    >
            <b-form-checkbox-group
	      v-model="filterOn"
	      class="mt-1 mb-0">
              <b-form-checkbox value="from">From</b-form-checkbox>
              <b-form-checkbox value="recipients">Recipients</b-form-checkbox>
              <b-form-checkbox value="subject">Subject</b-form-checkbox>
              <b-form-checkbox value="body">Message body</b-form-checkbox>
            </b-form-checkbox-group>
	  </b-form-group>
	</b-col>
      </b-row>
    </b-card>
    <b-table
      id="my-table"
      :items="messagesProvider"
      :fields="fields"
      :filter="filter"
      :filterIncludedFields="filterOn"
      @filtered="onFiltered"
      :per-page="perPage"
      :current-page="currentPage"
      >
      <template v-slot:cell(read)="row">
	<b-badge variant="primary">{{ row.item.read ? "" : "&emsp;" }}</b-badge>
      </template>
      <template v-slot:cell(tags)="row">
	<ul class="list-inline">
	  <li class="list-inline-item m-0" v-for="tag in row.item.tags">
	    <b-button
	      size="sm"
	      class="p-1"
	      @click="tagMessage(row.item, tag, 'remove')"
	      :variant="tag.variant"
	      >
	      {{ tag.unicode_symbol }}
	    </b-button>
	  </li>
	</ul>
      </template>
      <template v-slot:cell(addtag)="row">
	<b-button
	  size="sm"
	  v-b-toggle="'collapse-tags' + row.item.uuid"
	  variant="primary"
	  >
	  Add&nbsp;tag
	</b-button>
	<b-collapse :id="'collapse-tags' + row.item.uuid">
	  <b-card>
	    <ul class="list-unstyled">
	      <li v-for="tag in tags">
		<b-button
		  size="sm"
		  class="p-1"
		  @click="tagMessage(row.item, tag, 'add')"
		  :variant="tag.variant"
		  >
		  {{ tag.unicode_symbol }}&nbsp;{{ tag.label }}
		</b-button>
	      </li>
	    </ul>
	  </b-card>
	</b-collapse>
      </template>
      <template v-slot:cell(actions)="row">
	<b-button
	  size="sm"
	  variant="primary"
	  @click="row.toggleDetails"
	  >
          {{ row.detailsShowing ? 'Hide' : 'Show' }}
	</b-button>
      </template>
      <template v-slot:row-details="row">
	<message-content :message=row.item class="m-2 mb-4"></message-content>
      </template>
    </b-table>
  </div>

</div>
</template>


<script>
import Cookies from 'js-cookie'

import MessageContent from './MessageContent.vue'

var csrftoken = Cookies.get('csrftoken');

export default {
    name: "messages-table",
    components: {
	MessageContent,
    },
    data() {
	return {
	    accesses: null,
	    accountSelected: null,
	    perPage: 10,
	    currentPage: 1,
	    totalRows: 1,
	    fields: [
		{ key: 'read', label: '' },
		{ key: 'datetimestamp', label: 'On' },
		{ key: 'data.subject', label: 'Subject' },
		{ key: 'data.from', label: 'From' },
		{ key: 'data.recipients', label: 'Recipients' },
		{ key: 'tags', label: 'Tags' },
		{ key: 'addtag', label: '' },
		{ key: 'actions', label: '' }
	    ],
	    filter: null,
	    filterOn: [],
	    timePeriod: 'any',
	    timePeriodOptions: [
		{ text: 'Last week', value: 'week'},
		{ text: 'Last month', value: 'month'},
		{ text: 'Last year', value: 'year'},
		{ text: 'Any time', value: 'any'},
	    ]
	}
    },
    methods: {
	fetchAccounts () {
	    fetch('/mail/api/user_account_accesses')
		.then(stream => stream.json())
		.then(data => this.accesses = data.results)
		.catch(error => console.error(error))
	},
	fetchTags () {
	    fetch('/mail/api/user_tags')
		.then(stream => stream.json())
		.then(data => this.tags = data.results)
		.catch(error => console.error(error))
	},
	tagMessage (message, tag, action) {
	    fetch('/mail/api/stored_message/' + message.uuid + '/tag',
		  {
		      method: 'PATCH',
		      headers: {
			  "X-CSRFToken": csrftoken,
			  "Content-Type": "application/json; charset=utf-8"
		      },
		      body: JSON.stringify({
			  'tagpk': tag.pk,
			  'action': action
		      })
		  }
		 ).then(function(response) {
		     if (!response.ok) {
			 throw new Error('HTTP error, status = ' + response.status);
		     }
		 });

	    if (action == 'add') {
		// Prevent doubling by removing first, then (re)adding
		message.tags = message.tags.filter(function (item) { return item.pk !== tag.pk })
		message.tags.push(tag)
	    }
	    else if (action == 'remove') {
		message.tags.splice(message.tags.indexOf(tag), 1)
	    }
	},
	isSelected: function (selection) {
	    return selection === this.accountSelected
	},
	messagesProvider(ctx) {
	    var params = '?account=' + this.accountSelected
	    // Our API uses limit/offset pagination
	    params += '&limit=' + ctx.perPage + '&offset=' + ctx.perPage * (ctx.currentPage - 1)
	    // Add search time period
	    params += '&period=' + this.timePeriod
	    // Add search query (if it exists)
	    if (this.filter) {
		var filterlist = ['from', 'recipients', 'subject', 'body']
		if (this.filterOn.length > 0) {
		    filterlist = this.filterOn
		}

		filterlist.forEach((filterfield) => {
		    params += '&' + filterfield + '=' + this.filter
		});
	    }
	    const promise = fetch('/mail/api/stored_messages' + params)

	    return promise.then(stream => stream.json())
		.then(data => {
		    const items = data.results
		    this.totalRows = data.count
		    return items || []
		})
	},
	onFiltered(filteredItems) {
            this.totalRows = filteredItems.length
            this.currentPage = 1
	}
    },
    mounted() {
	this.fetchAccounts()
	this.fetchTags()
    },
}

</script>
