<template>
<div>

  <div v-if="accesses" class="m-2 mb-4">
    <b-button
      v-b-modal.modal-newdraft
      variant="primary"
      >
      Compose a new message
    </b-button>

    <b-modal
      id="modal-newdraft"
      size="xl"
      title="New message"
      hide-header-close
      no-close-on-escape
      no-close-on-backdrop
      >
      <message-composer></message-composer>
      <template v-slot:modal-footer="{ close, }">
	<b-button size="sm" variant="danger" @click="close()">
	  Close
	</b-button>
      </template>
    </b-modal>
  </div>

  <b-modal
    id="modal-resumedraft"
    size="xl"
    title="Rework draft"
    hide-header-close
    no-close-on-escape
    no-close-on-backdrop
    >
    <message-composer :draftmessage="draftMessageSelected"></message-composer>
    <template v-slot:modal-footer="{ close, }">
      <b-button size="sm" variant="danger" @click="close()">
	Close
      </b-button>
    </template>
  </b-modal>

  <b-modal
    id="modal-manage-tags"
    title="Manage your Tags"
    hide-header-close
    >
    <tag-list-editable :tags="tags" @fetchtags="fetchTags"></tag-list-editable>
    <template v-slot:modal-footer="{ close, }">
      <b-button size="sm" variant="danger" @click="close()">
	Done
      </b-button>
    </template>
  </b-modal>


  <div v-if="draftMessages.length > 0" class="m-2 mb-4">
    <h2>Message drafts to complete</h2>
    <table class="table">
      <tr>
	<th>From</th>
	<th>To</th>
	<th>Subject</th>
	<th>Status</th>
	<th>Actions</th>
      </tr>
      <tr
	v-for="draftmsg in draftMessages"
	>
	<td>{{ draftmsg.from_account }}</td>
	<td>{{ draftmsg.to_recipient }}</td>
	<td>{{ draftmsg.subject }}</td>
	<td>{{ draftmsg.status }}</td>
	<td>
	  <b-button
	    @click="showReworkDraftModal(draftmsg)"
	    size="sm"
	    class="text-white"
	    variant="warning"
	    >
	    Rework draft
	  </b-button>
	  <b-button
	    @click="deleteDraft(draftmsg.uuid)"
	    size="sm"
	    variant="danger"
	    >
	    Delete
	  </b-button>
	</td>
      </tr>
    </table>
  </div>

  <h2 class="m-2">Click on an account to view messages</h2>
  <table class="table mb-4">
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
      v-on:click="accountSelected = access.account"
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

  <div v-if="accountSelected" :key="accountSelected.pk">
    <b-card bg-variant="light">
      <b-row>
	<b-col class="col-lg-6">
	  <h2>Messages for <strong>{{ accountSelected.email }}</strong></h2>
	  <!-- <b-form-group -->
	  <!--   label="Auto refresh (minutes): " -->
	  <!--   label-cols-sm="4" -->
	  <!--   label-align-sm="right" -->
	  <!--   label-size="sm" -->
	  <!--   > -->
	  <!--   <b-form-radio-group -->
	  <!--     v-model="refreshMinutes" -->
	  <!--     :options="refreshMinutesOptions" -->
	  <!--     class="float-center" -->
	  <!--     > -->
	  <!--   </b-form-radio-group> -->
	  <!-- </b-form-group> -->
	  <small class="p-2">Last loaded: {{ lastLoaded }}</small>
	  <b-badge
	    class="p-2"
	    size="sm"
	    variant="primary"
	    @click="refreshMessages"
	    >
	    Refresh now
	  </b-badge>
	</b-col>
	<b-col class="col-lg-2">
	  <b-badge variant="primary" class="p-2">{{ totalRows }} messages</b-badge>
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
	  <b-form-group
	    label="Per page:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    >
	    <b-form-radio-group
	      v-model="perPage"
	      :options="perPageOptions"
	      class="float-center"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
      </b-row>
      <hr>

      <b-row class="mb-0">
	<b-col class="col-lg-1">
	  <strong>Restrict:</strong>
	</b-col>
	<b-col class="col-lg-5">
	  <b-form-group
	    label="Status:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    >
	    <b-form-radio-group
	      v-model="readStatus"
	      :options="readStatusOptions"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-5">
	  <b-form-group
	    label="Tag:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    >
	    <b-form-radio-group>
	      <b-form-radio v-model="tagRequired" value="any">Any</b-form-radio>
	      <b-form-radio v-model="tagRequired" v-for="tag in tags" :value="tag.pk" :key="tag.pk">
		<b-button size="sm" class="p-1" :variant="tag.variant">
		  {{ tag.unicode_symbol }}
		</b-button>
	      </b-form-radio>
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-1">
	  <b-button
	    size="sm"
	    class="pb-2"
	    @click="showManageTagsModal"
	    variant="primary"
	    >
	    <small>Manage your tags</small>
	  </b-button>
	</b-col>
      </b-row>
      <hr>
      <b-row class="mb-0">
	<b-col class="col-lg-1">
	  <strong>Search:</strong>
	</b-col>
	<b-col class="col-lg-6">
	  <b-form-group
	    label-cols-sm="3"
	    label="Filter:"
            label-align-sm="right"
            label-size="sm"
	    >
	    <b-input-group size="sm">
	      <b-form-input
		v-model="filter"
		debounce="250"
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
	    label="Period:"
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
      responsive
      show-empty
      :items="messagesProvider"
      :fields="fields"
      :filter="filter"
      :filterIncludedFields="filterOn"
      @filtered="onFiltered"
      :per-page="perPage"
      :current-page="currentPage"
      selectable
      @row-clicked="onMessageRowClicked"
      >
      <template v-slot:table-busy>
      	<div class="text-center text-primary my-2">
      	  <b-spinner class="align-middle"></b-spinner>
      	  <strong>Loading...</strong>
      	</div>
      </template>
      <template v-slot:head(tags)="row">
	Tags
      </template>
      <template v-slot:cell(read)="row">
	<b-badge variant="primary">{{ row.item.read ? "" : "&emsp;" }}</b-badge>
      </template>
      <template v-slot:cell(tags)="row">
	<ul class="list-inline">
	  <li class="list-inline-item m-0" v-for="tag in row.item.tags">
	    <b-button
	      size="sm"
	      class="p-1"
	      :variant="tag.variant"
	      >
	      {{ tag.unicode_symbol }}
	    </b-button>
	  </li>
	</ul>
      </template>
      <template v-slot:cell(actions)="row">
        <span v-if="row.detailsShowing">
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-down-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
	  </svg>
	</span>
	<span v-else>
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-right-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M12.14 8.753l-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
	  </svg>
	</span>
      </template>
      <template v-slot:row-details="row">
	<message-content
	  :message=row.item
	  :tags="tags"
	  :accountSelected="accountSelected"
	  class="m-2 mb-4"></message-content>
      </template>
    </b-table>

  </div>

</div>
</template>


<script>
import Cookies from 'js-cookie'

import MessageContent from './MessageContent.vue'

import MessageComposer from './MessageComposer.vue'

import TagListEditable from './TagListEditable.vue'

var csrftoken = Cookies.get('csrftoken');

export default {
    name: "messages-table",
    components: {
	MessageContent,
	MessageComposer,
	TagListEditable,
    },
    data() {
	return {
	    accesses: null,
	    accountSelected: null,
	    draftMessages: [],
	    draftMessageSelected: null,
	    queuedMessages: null,
	    messages: [],
	    perPage: 8,
	    perPageOptions: [ 8, 16, 32 ],
	    currentPage: 1,
	    totalRows: 1,
	    lastLoaded: null,
	    fields: [
		{ key: 'actions', label: '' },
		{ key: 'read', label: '' },
		{ key: 'datetimestamp', label: 'On' },
		{ key: 'data.subject', label: 'Subject' },
		{ key: 'data.from', label: 'From' },
		{ key: 'data.recipients', label: 'Recipients' },
		{ key: 'tags', },
	    ],
	    filter: null,
	    filterOn: [],
	    timePeriod: 'any',
	    timePeriodOptions: [
		{ text: 'Last week', value: 'week' },
		{ text: 'Last month', value: 'month' },
		{ text: 'Last year', value: 'year' },
		{ text: 'Any time', value: 'any' },
	    ],
	    readStatus: null,
	    readStatusOptions: [
		{ text: 'unread', value: false },
		{ text: 'read', value: true },
		{ text: 'all', value: null },
	    ],
	    refreshInterval: null,
	    refreshMinutes: 1,
	    refreshMinutesOptions: [ 1, 5, 15, 60 ],
	    tags: null,
	    tagRequired: 'any',
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
	fetchDrafts () {
	    fetch('/mail/api/composed_messages?status=draft')
		.then(stream => stream.json())
		.then(data => this.draftMessages = data.results)
		.catch(error => console.error(error))
	},
	showManageTagsModal () {
	    this.$bvModal.show('modal-manage-tags')
	},
	showReworkDraftModal (draftmsg) {
	    this.draftMessageSelected = draftmsg
	    this.$bvModal.show('modal-resumedraft')
	},
	deleteDraft (uuid) {
	    if (confirm("Are you sure you want to delete this draft?")) {
		fetch('/mail/api/composed_message/' + uuid + '/delete',
		      {
			  method: 'DELETE',
			  headers: {
			      "X-CSRFToken": csrftoken,
			  }
		      }
		     )
		    .then(response => {
			if (response.ok) {
			    this.fetchDrafts()
			}
		    })
		    .catch(error => console.error(error))
	    }
	},
	isSelected: function (selection) {
	    if (this.accountSelected) {
		return selection === this.accountSelected.email
	    }
	    return false
	},
	messagesProvider (ctx) {
	    var params = '?account=' + this.accountSelected.email
	    // Our API uses limit/offset pagination
	    params += '&limit=' + ctx.perPage + '&offset=' + ctx.perPage * (ctx.currentPage - 1)
	    // Add search time period
	    params += '&period=' + this.timePeriod
	    if (this.readStatus !== null) {
		params += '&read=' + this.readStatus
	    }
	    if (this.tagRequired !== 'any') {
		params += '&tag=' + this.tagRequired
	    }
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

	    var now = new Date()
	    this.lastLoaded = now.toISOString()

	    return promise.then(stream => stream.json())
		.then(data => {
		    const items = data.results
		    this.totalRows = data.count
		    return items || []
		})
	},
	refreshMessages () {
	    this.messagesProvider({
		'perPage': this.perPage,
		'currentPage': this.currentPage
	    })
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	onFiltered(filteredItems) {
            this.totalRows = filteredItems.length
            this.currentPage = 1
	},
	onMessageRowClicked (item, index) {
	    this.$set(item, '_showDetails', !item._showDetails)
	}
    },
    mounted() {
	this.fetchAccounts()
	this.fetchTags()
	this.fetchDrafts()
	this.$root.$on('bv::modal::hide', (bvEvent, modalId) => {
	    if (bvEvent.componentId === 'modal-newdraft' ||
		bvEvent.componentId === 'modal-resumedraft' ||
		bvEvent.componentId === 'modal-reply' ||
		bvEvent.componentId === 'modal-forward') {
		this.fetchDrafts()
	    }
	})
	// this.refreshInterval = setInterval(this.refreshMessages, this.refreshMinutes * 1000)
    },
    // beforeDestroy() {
    // 	clearInterval(this.refreshInterval)
    // },
    watch: {
	accountSelected: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	timePeriod: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	filterOn: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	readStatus: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	tagRequired: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	// refreshMinutes: function () {
	//     clearInterval(this.refreshInterval)
	//     this.refreshInterval = setInterval(this.refreshMessages, this.refreshMinutes * 1000)
	// }
    }
}

</script>
