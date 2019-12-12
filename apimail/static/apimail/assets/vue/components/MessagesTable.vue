<template>
<div class="overflow-auto">
  <b-pagination
    v-model="currentPage"
    :total-rows="totalRows"
    :per-page="perPage"
    aria-controls="my-table"
    >
  </b-pagination>
  <b-table
    id="my-table"
    :items="messagesProvider"
    :fields="fields"
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
	}
    },
    methods: {
	messagesProvider(ctx) {
	    // Our API uses limit/offset pagination
	    const params = '?limit=' + ctx.perPage + '&offset=' + ctx.perPage * (ctx.currentPage - 1)
	    console.log(ctx.perPage)
	    console.log(ctx.currentPage)
	    console.log(ctx.perPage * (ctx.currentPage - 1))
	    const promise = fetch('/mail/api/stored_messages' + params)

	    return promise.then(stream => stream.json())
		.then(data => {
		    const items = data.results
		    this.totalRows = data.count
		    return items || []
		})
	}
    }
}

</script>
