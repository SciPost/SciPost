
<template>
<div>
  <div v-if="currentSendingAccesses && currentSendingAccesses.length > 0" class="mb-4">
    <b-button-toolbar aria-label="apimail button toolbar">
      <b-button-group class="mx-1">
	<b-button
	  v-b-modal.modal-newdraft
	  variant="primary"
	  >
	  New message
	</b-button>
      </b-button-group>
      <b-button-group class="mx-1">
	<b-button
	  @click="showManageTagsModal"
	  variant="primary"
	  >
	  Manage your tags
	</b-button>
      </b-button-group>
    </b-button-toolbar>
    <b-modal
      id="modal-newdraft"
      size="xl"
      title="New message"
      hide-header-close
      no-close-on-escape
      no-close-on-backdrop
      >
      <message-composer
	:accountSelected="accountSelected"
	>
      </message-composer>
      <template v-slot:modal-header="{ close, }">
	<h1>Compose a new email message</h1>
	<b-button variant="danger" class="px-2 py-1" @click="close()">
	  Discard/Close
	</b-button>
      </template>
      <template v-slot:modal-footer="{ close, }">
	<b-button variant="danger" class="px-2 py-1" @click="close()">
	  Discard/Close
	</b-button>
      </template>
    </b-modal>
  </div>

  <b-modal
    id="modal-resumedraft"
    size="xl"
    title="Rework draft"
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


  <div v-if="draftMessages && draftMessages.length > 0" class="m-2 mb-4">
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
	<td>{{ draftmsg.from_email }}</td>
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

  <div v-if="queuedMessages && queuedMessages.length > 0" class="m-2 mb-4">
    <h2>Messages in sending queue</h2>
    <table class="table">
      <tr>
	<th>On</th>
	<th>From</th>
	<th>To</th>
	<th>Subject</th>
	<th>Status</th>
      </tr>
      <tr
	v-for="queuedmsg in queuedMessages"
	>
	<td>{{ queuedmsg.created_on }}</td>
	<td>{{ queuedmsg.from_email }}</td>
	<td>{{ queuedmsg.to_recipient }}</td>
	<td>{{ queuedmsg.subject }}</td>
	<td>{{ queuedmsg.status }}</td>
      </tr>
    </table>
  </div>

  <div class="accounts-table">
    <div class="bg-primary text-white pb-2">
      <h1 class="p-2 mb-0 text-center">Your email accounts</h1>
      <div class="text-center"><em>(click on a row to see messages)</em></div>
    </div>
    <table
      class="table mb-4"
      selectable
      select-mode="single"
      >
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
  </div>

  <div v-if="accountSelected" :key="accountSelected.pk">
    <b-card bg-variant="light">
      <h2 class="text-center mb-2">Messages&nbsp;for&emsp;<strong>{{ accountSelected.email }}</strong></h2>
      <hr class="my-2">
      <b-row class="mb-0">
	<b-col class="col-lg-6">
	  <small class="p-2">Last loaded: {{ lastLoaded }}</small>
	  <b-badge
	    class="p-2"
	    size="sm"
	    variant="primary"
	    @click="refreshMessages"
	    >
	    Refresh now
	  </b-badge>
	  <div v-if="loadError">
	    <small class="bg-danger text-white mx-2 p-1">A network problem occurred on {{ lastFetched }}</small>
	  </div>
	</b-col>
	<b-col class="col-lg-6">
	  <b-form-group
	    label="Refresh interval: "
	    label-cols-sm="6"
	    label-align-sm="right"
	    label-size="sm"
	    >
	    <b-form-radio-group
	      v-model="refreshMinutes"
	      buttons
	      button-variant="outline-primary"
	      size="sm"
	      :options="refreshMinutesOptions"
	      class="float-center"
	      >
	      &nbsp;mins
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
      </b-row>
      <hr class="hr-lightweight mt-1 mb-2">
      <b-row class="mb-0">
	<b-col class="col-lg-1">
	  <strong>Restrict:</strong>
	</b-col>
	<b-col class="col-lg-4">
	  <b-form-group
	    label="Last: "
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    class="mb-0"
	    >
	    <b-form-radio-group
	      v-model="timePeriod"
	      buttons
	      button-variant="outline-primary"
	      size="sm"
	      :options="timePeriodOptions"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-4">
	  <b-form-group
	    label="Status:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    class="mb-0"
	    >
	    <b-form-radio-group
	      v-model="readStatus"
	      buttons
	      button-variant="outline-primary"
	      size="sm"
	      :options="readStatusOptions"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-3">
	  <b-form-group
	    label="Flow:"
	    label-cols-sm="3"
	    label-align-sm="right"
	    label-size="sm"
	    class="mb-0"
	    >
	    <b-form-radio-group
	      v-model="flowDirection"
	      buttons
	      button-variant="outline-primary"
	      size="sm"
	      :options="flowDirectionOptions"
	      >
	    </b-form-radio-group>
	  </b-form-group>
	</b-col>
      </b-row>
      <hr class="hr-lightweight mt-1 mb-2">
      <b-row class="mb-0">
	<b-col class="col-lg-1">
	  <strong>Tags:</strong>
	</b-col>
	<b-col class="col-lg-9">
	  <b-form-group
	    label-align-sm="right"
	    label-size="sm"
	    >
	    <b-form-checkbox-group>
	      <b-form-checkbox v-model="tagsRequired" v-for="tag in tags" :value="tag.pk" :key="tag.pk">
		<b-button size="sm" class="p-1" :style="'background-color: ' + tag.bg_color">
		  <small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
		</b-button>
	      </b-form-checkbox>
	    </b-form-checkbox-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-2">
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
      <hr class="hr-lightweight mt-1 mb-2">
      <b-row class="mb-0">
	<b-col class="col-lg-6">
	  <b-form-group>
	    <b-input-group size="sm">
	      <b-form-input
		v-model="filter"
		debounce="250"
		type="search"
		id="filterInput"
		placeholder="Type to filter"
		>
	      </b-form-input>
	      <b-input-group-append>
		<b-button :disabled="!filter" @click="filter = ''">Clear</b-button>
	      </b-input-group-append>
	    </b-input-group>
	  </b-form-group>
	</b-col>
	<b-col class="col-lg-6 mb-0">
	  <b-form-group
            description="Leave all unchecked to filter on all fields"
	    class="mb-0"
	    >
            <b-form-checkbox-group
	      v-model="filterOn"
	      buttons
	      button-variant="outline-primary"
	      class="mt-1 mb-0"
	      size="sm"
	      >
              <b-form-checkbox value="from">From</b-form-checkbox>
              <b-form-checkbox value="recipients">Recipients</b-form-checkbox>
              <b-form-checkbox value="subject">Subject</b-form-checkbox>
              <b-form-checkbox value="body">Body</b-form-checkbox>
              <b-form-checkbox value="attachment">Attachments</b-form-checkbox>
            </b-form-checkbox-group>
	  </b-form-group>
	</b-col>
      </b-row>
    </b-card>
    <div v-if="threadOf" class="bg-primary text-white">
      <b-row class="mt-2 p-2">
	<b-col class="my-auto"><h2 class="my-0 px-2">Thread focusing is active</h2></b-col>
	<b-col class="mx-auto">
	  <b-button class="text-white float-right" variant="warning" @click="unfocusThread()">
	    <strong>Turn off</strong>
	  </b-button>
	</b-col>
      </b-row>
    </div>
    <b-table
      id="my-table"
      class="mb-0"
      responsive
      show-empty
      :items="messagesProvider"
      :fields="fields"
      :filter="filter"
      :filterIncludedFields="filterOn"
      @filtered="onFiltered"
      :per-page="perPage"
      :current-page="currentPage"
      @row-clicked="onMessageRowClicked"
      >
      <template v-slot:table-busy>
      	<div class="text-center text-primary my-2">
      	  <b-spinner class="align-middle"></b-spinner>
      	  <strong>Loading...</strong>
      	</div>
      </template>
      <template v-slot:head(tab)="row">
	<span v-if="tabbedMessages.length > 0">
	  Tab
	</span>
      </template>
      <template v-slot:head(tags)="row">
	Tags
      </template>
      <template v-slot:cell(tab)="row">
	<span v-if="isInTabbedMessages(row.item.uuid)">
	  {{ tabbedMessages.length - indexInTabbedMessages(row.item.uuid) }}
	</span>
      </template>
      <template v-slot:cell(read)="row">
	<span v-if="!row.item.read">
	  <b-badge variant="primary">&emsp;</b-badge>
	</span>
      </template>
      <template v-slot:cell(tags)="row">
	<ul class="list-inline">
	  <li class="list-inline-item m-0" v-for="tag in row.item.tags">
	    <b-button
	      size="sm"
	      class="p-1"
	      :style="'background-color: ' + tag.bg_color"
	      >
	      <small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
	    </b-button>
	  </li>
	</ul>
      </template>
    </b-table>
    <b-card bg-variant="light" class="pb-0">
      <b-row class="mb-0">
	<b-col class="col-lg-4">
	  <div class="text-center">
	    <b-button size="sm" variant="info" class="p-2">{{ totalRows }} messages</b-button>
	  </div>
	</b-col>
	<b-col class="col-lg-4">
	  <b-pagination
	    v-model="currentPage"
	    :total-rows="totalRows"
	    :per-page="perPage"
	    class="m-1"
	    size="sm"
	    align="center"
	    aria-controls="my-table"
	    >
	  </b-pagination>
	</b-col>
	<b-col class="col-lg-4">
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
    </b-card>
    <b-tabs
      id="message-tabs"
      v-model="tabIndex"
      class="mt-4"
      :key="tabsKey"
      lazy
      >
      <b-tab
	v-for="(message, index) in tabbedMessages"
	:key="'tab-' + message.uuid"
	>
	<template v-slot:title>
	  {{ tabbedMessages.length - index }}
	  <b-button v-if="!threadOf" size="sm" variant="light" class="float-right ml-2 p-0" @click="closeTab(message.uuid)">
	    <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-x" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	      <path fill-rule="evenodd" d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
	    </svg>
	  </b-button>
	  <br>
	</template>
	<div v-if="!threadOf">
	  <b-button class="m-2" size="sm" variant="primary" @click="focusOnThread(message.uuid)">
	    Focus on this message's thread
	  </b-button>
	</div>
	<message-content
	  :message="message"
	  :tags="tags"
	  :accountSelected="accountSelected"
	  class="m-2 mb-4">
	</message-content>
      </b-tab>
    </b-tabs>
  </div>
</div>
</template>


<script>
import Cookies from 'js-cookie'

//import MessageContent from './MessageContent.vue'
const MessageContent = () => import('./MessageContent.vue');

//import MessageComposer from './MessageComposer.vue'
const MessageComposer = () => import('./MessageComposer.vue');

//import TagListEditable from './TagListEditable.vue'
const TagListEditable = () => import('./TagListEditable.vue');

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
	    currentSendingAccesses: null,
	    accountSelected: null,
	    draftMessages: [],
	    draftMessageSelected: null,
	    queuedMessages: null,
	    tabbedMessages: [],
	    perPage: 8,
	    perPageOptions: [ 8, 16, 32 ],
	    currentPage: 1,
	    totalRows: 1,
	    lastFetched: null,
	    lastLoaded: null,
	    loadError: false,
	    fields: [
		{ key: 'tab', label: '' },
		{ key: 'read', label: '' },
		{ key: 'datetimestamp', label: 'On' },
		{ key: 'data.subject', label: 'Subject' },
		{ key: 'data.from', label: 'From' },
		{ key: 'data.recipients', label: 'Recipients' },
		{ key: 'tags', },
	    ],
	    filter: null,
	    filterOn: [],
	    threadOf: null,
	    timePeriod: 'any',
	    timePeriodOptions: [
		{ text: 'week', value: 'week' },
		{ text: 'month', value: 'month' },
		{ text: 'year', value: 'year' },
		{ text: 'any', value: 'any' },
	    ],
	    readStatus: null,
	    readStatusOptions: [
		{ text: 'unread', value: false },
		{ text: 'read', value: true },
		{ text: 'all', value: null },
	    ],
	    flowDirection: 'in',
	    flowDirectionLastNotNull: 'in',
	    flowDirectionOptions: [
		{ text: 'in', value: 'in' },
		{ text: 'out', value: 'out' },
		{ text: 'both', value: null }
	    ],
	    refreshInterval: null,
	    refreshMinutes: 1,
	    refreshMinutesOptions: [ 1, 5, 15 ],
	    tabIndex: 0,
	    tabsKey: 0,
	    tags: null,
	    tagsRequired: [],
	}
    },
    methods: {
	fetchAccounts () {
	    fetch('/mail/api/user_account_accesses')
		.then(stream => stream.json())
		.then(data => this.accesses = data.results)
		.catch(error => console.error(error))
	},
	fetchCurrentSendingAccounts () {
	    fetch('/mail/api/user_account_accesses?current=true&cansend=true')
		.then(stream => stream.json())
		.then(data => this.currentSendingAccesses = data.results)
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
	fetchQueued () {
	    fetch('/mail/api/composed_messages?status=queued')
		.then(stream => stream.json())
		.then(data => this.queuedMessages = data.results)
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
	    if (!this.accountSelected) return []

	    var params = '?account=' + this.accountSelected.email
	    // Our API uses limit/offset pagination
	    params += '&limit=' + ctx.perPage + '&offset=' + ctx.perPage * (ctx.currentPage - 1)
	    if (this.threadOf) {
		params += '&thread_of_uuid=' + this.threadOf
	    }
	    // Add flow direction
	    if (this.flowDirection) {
		params += '&flow=' + this.flowDirection
	    }
	    // Add search time period
	    params += '&period=' + this.timePeriod
	    if (this.readStatus !== null) {
		params += '&read=' + this.readStatus
	    }
	    this.tagsRequired.forEach((tag) => {
		params += '&tag=' + tag
	    })
	    // Add search query (if it exists)
	    if (this.filter) {
		var filterlist = ['from', 'recipients', 'subject', 'body', 'attachment']
		if (this.filterOn.length > 0) {
		    filterlist = this.filterOn
		}

		filterlist.forEach((filterfield) => {
		    params += '&' + filterfield + '=' + this.filter
		});
	    }
	    const promise = fetch('/mail/api/stored_messages' + params)

	    var now = new Date()

	    return promise.then(response => {
		if (response.ok) {
		    this.lastLoaded = now.toISOString()
		    this.loadError = false
		}
		else {
		    this.lastFetched = now.toISOString()
		    this.loadError = true
		}
		return response.json()
	    })
		.then(data => {
		    const items = data.results
		    this.totalRows = data.count
		    if (this.threadOf) {
			this.tabbedMessages = items
		    }
		    return items || []
		})
		.catch(error => console.error(error))
	},
	refreshMessages () {
	    this.messagesProvider({
		'perPage': this.perPage,
		'currentPage': this.currentPage
	    })
	    this.$root.$emit('bv::refresh::table', 'my-table')
	    this.fetchQueued()
	},
	onFiltered(filteredItems) {
            this.totalRows = filteredItems.length
            this.currentPage = 1
	},
	indexInTabbedMessages (uuid) {
	    for (let i = 0; i < this.tabbedMessages.length; i++) {
		if (this.tabbedMessages[i].uuid == uuid) {
		    return i
		}
	    }
	    return -1
	},
	isInTabbedMessages (uuid) {
	    return this.indexInTabbedMessages(uuid) != -1
	},
	onMessageRowClicked (item, index) {
	    if (!this.isInTabbedMessages(item.uuid)) {
	    	this.tabbedMessages.push(item)
	    }
	    this.tabIndex = this.indexInTabbedMessages(item.uuid)
	    this.tabsKey = 1 - this.tabsKey // force re-render of b-tabs id="message-tabs"
	},
	focusOnThread (uuid) {
	    this.threadOf = uuid
	},
	unfocusThread () {
	    this.threadOf = null
	    this.tabbedMessages = []
	    this.tabIndex = 0
	},
	closeTab(uuid) {
	    for (let i = 0; i < this.tabbedMessages.length; i++) {
		if (this.tabbedMessages[i].uuid === uuid) {
		    this.tabbedMessages.splice(i, 1)
		    this.tabIndex = 0
		}
            }
	},
    },
    mounted() {
	this.fetchAccounts()
	this.fetchCurrentSendingAccounts()
	this.fetchTags()
	this.fetchDrafts()
	this.fetchQueued()
	this.$root.$on('bv::modal::hide', (bvEvent, modalId) => {
	    if (bvEvent.componentId === 'modal-newdraft' ||
		bvEvent.componentId === 'modal-resumedraft' ||
		bvEvent.componentId === 'modal-reply' ||
		bvEvent.componentId === 'modal-forward') {
		this.fetchDrafts()
	    }
	})
 	this.refreshInterval = setInterval(this.refreshMessages, this.refreshMinutes * 60000)
    },
    beforeDestroy() {
    	clearInterval(this.refreshInterval)
    },
    watch: {
	accountSelected: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	threadOf: function () {
	    if (this.threadOf == null) {
		this.flowDirection = this.flowDirectionLastNotNull
	    }
	    else {
		this.flowDirectionLastNotNull = this.flowDirection
		this.flowDirection = null
	    }
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
	flowDirection: function () {
	    if (this.flowDirection != null) {
		this.flowDirectionLastNotNull = this.flowDirection
	    }
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	tagsRequired: function () {
	    this.$root.$emit('bv::refresh::table', 'my-table')
	},
	accountSelected: function () {
	    this.tabbedMessages = []
	},
	tabbedMessages: function () {
	    if (this.threadOf) {
		this.tabIndex = this.indexInTabbedMessages(this.threadOf)
		this.tabsKey = 1 - this.tabsKey // force re-render of b-tabs id="message-tabs"
	    }
	},
	refreshMinutes: function () {
	    clearInterval(this.refreshInterval)
	    this.refreshInterval = setInterval(this.refreshMessages, this.refreshMinutes * 60000)
	},
    }
}

</script>

<style>
  .accounts-table {
  background-color: #d3e3f6;
  }
  .highlight {
  background-color: #496bb6;
  color: white;
  }
  .hr-lightweight {
  background: #808080;
  color: #808080;
  height: 1px;
  }
</style>
