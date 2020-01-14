<template>
<div class="overflow-auto">
  <b-card bg-variant="light">
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
  <b-pagination
    v-model="currentPage"
    :total-rows="totalRows"
    :per-page="perPage"
    class="m-2"
    align="center"
    aria-controls="my-table"
    >
  </b-pagination>
  <p align="center">{{ totalRows }} messages</p>
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
    <template v-slot:cell(actions)="row">
      <b-button size="sm" @click="row.toggleDetails">
        {{ row.detailsShowing ? 'Hide' : 'Show' }}
      </b-button>
    </template>
    <template v-slot:row-details="row">
      <message-content :message=row.item class="m-2 mb-4"></message-content>
    </template>
  </b-table>
</div>
</template>


<script>
import MessageContent from './MessageContent.vue'

export default {
    name: "messages-table",
    components: {
	MessageContent,
    },
    data() {
	return {
	    perPage: 10,
	    currentPage: 1,
	    totalRows: 1,
	    fields: [
		{ key: 'datetimestamp', label: 'On' },
		{ key: 'data.subject', label: 'Subject' },
		{ key: 'data.from', label: 'From' },
		{ key: 'data.recipients', label: 'Recipients' },
		{ key: 'actions', label: 'Actions' }
	    ],
	    filter: null,
	    filterOn: [],
	    timePeriod: 'any',
	    timePeriodOptions: [
		{ 'text': 'Last week', value: 'week'},
		{ 'text': 'Last month', value: 'month'},
		{ 'text': 'Last year', value: 'year'},
		{ 'text': 'Any time', value: 'any'},
	    ]
	}
    },
    methods: {
	messagesProvider(ctx) {
	    // Our API uses limit/offset pagination
	    var params = '?limit=' + ctx.perPage + '&offset=' + ctx.perPage * (ctx.currentPage - 1)
	    // Add search time period
	    params += '&' + 'period=' + this.timePeriod
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
    }
}

</script>
