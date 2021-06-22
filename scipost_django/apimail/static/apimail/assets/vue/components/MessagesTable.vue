
<template>
<div>
  <div v-if="currentSendingAccesses && currentSendingAccesses.length > 0" class="mb-4">
    <div class="btn-toolbar" role="toolbar" aria-label="apimail button toolbar">
      <div class="btn-group mx-1">
	<button
	  type="button"
	  class="btn btn-primary"
	  data-bs-toggle="modal"
	  data-bs-target="#modal-newdraft"
	  >
	  New message
	</button>
      </div>
      <div class="btn-group mx-1">
	<button
	  type="button"
	  class="btn btn-primary"
	  data-bs-toggle="modal"
	  data-bs-target="#modal-manage-tags"
	  >
	  Manage your tags
	</button>
      </div>
    </div>
    <div
      class="modal fade"
      id="modal-newdraft"
      >
      <div class="modal-dialog modal-xl">
	<div class="modal-content">
	  <div class="modal-header">
	    <h1 class="modal-title">
	      Compose a new email message
	    </h1>
	    <button
	      type="button"
	      class="btn-close"
	      data-bs-dismiss="modal"
	      aria-label="Close">
	    </button>
	  </div>
	  <div class="modal-body">
	    <message-composer
	      :accountSelected="accountSelected"
	      >
	    </message-composer>
	  </div>
	  <div class="modal-footer">
	    <button
	      type="button"
	      class="btn btn-danger px-2 py-1"
	      data-bs-dismiss="modal"
	      >
	      Discard/Close
	    </button>
	  </div>
	</div>
      </div>
    </div>
  </div>

  <div
    class="modal fade"
    id="modal-manage-tags"
    >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
	<div class="modal-header">
	  <h1 class="modal-title">
	    Manage your Tags
	  </h1>
	  <button
	    type="button"
	    class="btn-close"
	    data-bs-dismiss="modal"
	    aria-label="Close">
	  </button>
	</div>
	<div class="modal-body">
	  <tag-list-editable
	    :tags="tags"
	    @fetchtags="fetchTags"
	    >
	  </tag-list-editable>
	</div>
	<div class="modal-footer">
	  <button
	    type="button"
	    class="btn btn-danger px-2 py-1"
	    data-bs-dismiss="modal"
	    >
	    Discard/Close
	  </button>
	</div>
      </div>
    </div>
  </div>



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
	:key="draftmsg.uuid"
	>
	<td>{{ draftmsg.from_email }}</td>
	<td>{{ draftmsg.to_recipient }}</td>
	<td>{{ draftmsg.subject }}</td>
	<td>{{ draftmsg.status }}</td>
	<td>
	  <button
	    type="button"
	    class="btn btn-sm btn-warning"
	    @click="showReworkDraftModal(draftmsg)"
	    >
	    Rework draft
	  </button>
	  <button
	    type="button"
	    class="btn btn-sm btn-danger"
	    @click="deleteDraft(draftmsg.uuid)"
	    >
	    Delete
	  </button>
	</td>
      </tr>
    </table>
  </div>

  <div
    class="modal fade"
    id="modal-resumedraft"
    >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
	<div class="modal-header">
	  <h1 class="modal-title">
	    Message draft
	  </h1>
	  <button
	    type="button"
	    class="btn-close"
	    data-bs-dismiss="modal"
	    aria-label="Close">
	  </button>
	</div>
	<div class="modal-body">
	  <message-composer
	    :draftmessage="draftMessageSelected"
	    >
	  </message-composer>
	</div>
	<div class="modal-footer">
	  <button
	    type="button"
	    class="btn btn-danger px-2 py-1"
	    data-bs-dismiss="modal"
	    >
	    Discard/Close
	  </button>
	</div>
      </div>
    </div>
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
	:class="{'highlight': isSelected(access.account.email)}"
	@click="accountSelected = access.account"
	@change=""
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
    <div class="card text-dark bg-light">
      <div class="card-header">
	<h2 class="text-center mb-2">Messages&nbsp;for&emsp;<strong>{{ accountSelected.email }}</strong></h2>
      </div>
      <div class="card-body">
	<div class="row mb-0">
	  <div class="col col-lg-6">
	    <small class="p-2">Last loaded: {{ lastLoaded }}</small>
	    <span
	      class="badge bg-primary p-2"
	      @click="fetchMessages"
	      >
	      Refresh now
	    </span>
	    <div v-if="loadError">
	      <small class="bg-danger text-white mx-2 my-1 p-1">
		A network problem occurred on {{ lastFetched }}
	      </small>
	    </div>
	  </div>
	  <div class="col col-lg-6">
	    <div class="row">
	      <div class="col">
		Refresh interval:
	      </div>
	      <div class="col">
		<div
		  v-for="refreshOption in refreshMinutesOptions"
		  class="form-check form-check-inline"
		  >
		  <input
		    class="form-check-input"
		    type="radio"
		    name="refreshMinutesRadio"
		    v-model="refreshMinutes"
		    :value="refreshOption"
		    :id="'refreshOption' + refreshOption"
		    >
		  <label
		    class="form-check-label"
		    for="'refreshOption' + refreshOption"
		    >
		    {{ refreshOption }}
		  </label>
		</div>
	      </div>
	      <div class="col">
		minutes
	      </div>
	    </div>
	  </div>
	</div>
	<hr class="hr-lightweight mt-1 mb-2">
	<div class="row mb-0">
	  <div class="col col-lg-4">
	    <div>
	      <strong>Last:</strong>
	    </div>
	    <div
	      v-for="timePeriodOption in timePeriodOptions"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="radio"
		name="timePeriodRadio"
		v-model="timePeriod"
		:value="timePeriodOption.value"
		:id="'timePeriodOption' + timePeriodOption.value"
		>
	      <label
		class="form-check-label"
		for="'timePeriodOption' + timePeriodOption.value"
		>
		{{ timePeriodOption.text }}
	      </label>
	    </div>
	  </div>
	  <div class="col col-lg-4">
	    <div>
	      <strong>Status:</strong>
	    </div>
	    <div
	      v-for="readStatusOption in readStatusOptions"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="radio"
		name="readStatusRadio"
		v-model="readStatus"
		:value="readStatusOption.value"
		:id="'readStatusOption' + readStatusOption.value"
		>
	      <label
		class="form-check-label"
		for="'readStatusOption' + readStatusOption.value"
		>
		{{ readStatusOption.text }}
	      </label>
	    </div>
	  </div>
	  <div class="col col-lg-4">
	    <div>
	      <strong>Flow:</strong>
	    </div>
	    <div
	      v-for="flowDirectionOption in flowDirectionOptions"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="radio"
		name="flowDirectionRadio"
		v-model="flowDirection"
		:value="flowDirectionOption.value"
		:id="'flowDirectionOption' + flowDirectionOption.value"
		>
	      <label
		class="form-check-label"
		for="'flowDirectionOption' + flowDirectionOption.value"
		>
		{{ flowDirectionOption.text }}
	      </label>
	    </div>
	  </div>
	</div>
	<hr class="hr-lightweight mt-1 mb-2">
	<div class="row mb-0">
	  <div class="col col-lg-1">
	    <strong>Tags:</strong>
	  </div>
	  <div class="col col-lg-9">
	    <div
	      v-for="tag in tags"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="checkbox"
		v-model="tagsRequired"
		:value="tag.pk"
		:key="tag.pk"
		>
	      <button
		type="button"
		class="btn btn-sm p-1"
		:style="'background-color: ' + tag.bg_color"
		>
		<small :style="'color: ' + tag.text_color">
		  {{ tag.label }}
		</small>
	      </button>
	    </div>
	  </div>
	  <div class="col col-lg-2">
	    <button
	      type="button"
	      class="btn btn-sm btn-primary pb-2"
	      data-bs-toggle="modal"
	      data-bs-target="#modal-manage-tags"
	      >
	      <small>Manage your tags</small>
	    </button>
	  </div>
	</div>
	<hr class="hr-lightweight mt-1 mb-2">
	<div class="row mb-0">
	  <div class="col col-lg-6">
	    <div class="input-group mb-3">
	      <input
		type="text"
		class="form-control"
		v-model="filter"
		placeholder="Type to filter"
		>
	      <button
		:disabled="!filter"
		@click="filter = ''"
		>
		Clear
	      </button>
	    </div>
	  </div>
	  <div class="col col-lg-6 mb-0">
	    <div
	      v-for="filterOnOption in filterOnOptions"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="checkbox"
		v-model="filterOn"
		:value="filterOnOption.value"
		id="'filterOnOption' + filterOnOption.value"
		>
	      <label
		class="form-check-label"
		for="'filterOnOption' + filterOnOption.value"
		>
		{{ filterOnOption.text }}
	      </label>
	    </div>
	    <div>
	      Leave all unchecked to filter on all fields
	    </div>
	  </div>
	</div>
      </div>
    </div>


    <div v-if="threadOf" class="bg-primary text-white">
      <div class="row mt-2 p-2">
	<div class="col my-auto"><h2 class="my-0 px-2">Thread focusing is active</h2></div>
	<div class="col mx-auto">
	  <button
	    type="button"
	    class="btn btn-warning text-white float-right"
	    @click="unfocusThread()"
	    >
	    <strong>Turn off</strong>
	  </button>
	</div>
      </div>
    </div>

    <table class="table mb-0">
      <thead>
	<tr>
	  <th v-if="tabbedMessages.length > 0" scope="col">
	    Tab
	  </th>
	  <th scope="col"></th>
	  <th scope="col">On</th>
	  <th scope="col">Subject</th>
	  <th scope="col">From</th>
	  <th scope="col">Recipients</th>
	  <th scope="col">Tags</th>
	</tr>
      </thead>
      <tbody>
	<tr
	  v-for="message in messages"
	  :key="message.uuid"
	  @click="onMessageRowClicked(message)"
	  >
	  <td v-if="tabbedMessages.length > 0">
	    <span v-if="isInTabbedMessages(message.uuid)">
	      {{ tabbedMessages.length - indexInTabbedMessages(message.uuid) }}
	    </span>
	  </td>
	  <td>
	    <span v-if="!message.read">
	      <span class="badge bg-primary">&emsp;</span>
	    </span>
	  </td>
	  <td>{{ message.datetimestamp }}</td>
	  <td>{{ message.data.subject }}</td>
	  <td>{{ message.data.from }}</td>
	  <td>{{ message.data.recipients }}</td>
	  <td>
	    <ul class="list-inline">
	      <li class="list-inline-item m-0" v-for="tag in message.tags">
		<button
		  type="button"
		  class="btn btn-sm p-1"
		  :style="'background-color: ' + tag.bg_color"
		  >
		  <small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
		</button>
	      </li>
	    </ul>
	  </td>
	</tr>
      </tbody>
    </table>

    <div class="card text-dark bg-light pb-0">
      <div class="card-body">
	<div class="row mb-0">
	  <div class="col col-lg-4">
	    <div class="text-center">
	      <button
		type="button"
		class="btn btn-sm btn-info p-2"
		>
		{{ totalRows }} messages
	      </button>
	    </div>
	  </div>
	  <div class="col col-lg-4">
	    <div class="input-group mb-3">
	      <span class="input-group-text">Page</span>
	      <input
		type="text"
		class="form-control"
		v-model="currentPage"
		>
	    </div>
	  </div>
	  <div class="col col-lg-4">
	    <div>
	      <strong>Per page:</strong>
	    </div>
	    <div
	      v-for="perPageOption in perPageOptions"
	      class="form-check form-check-inline"
	      >
	      <input
		class="form-check-input"
		type="radio"
		name="perPageRadio"
		v-model="perPage"
		:value="perPageOption"
		:id="'perPageOption' + perPageOption"
		>
	      <label
		class="form-check-label"
		for="'perPageOption' + perPageOption"
		>
		{{ perPageOption }}
	      </label>
	    </div>
	  </div>
	</div>
      </div>
    </div>

    <ul
      class="nav nav-tabs mt-4"
      role="tablist"
      id="message-tabs"
      >
      <li
	v-for="(message, index) in tabbedMessages"
	class="nav-item"
	role="presentation"
	:key="'li-' + message.uuid"
	>
	<button
	  class="nav-link"
	  :class="tabIndex === index ? 'active' : ''"
	  data-bs-toggle="tab"
	  :data-bs-target="'#tab-' + message.uuid"
	  type="button"
	  role="tab"
	  >
	  {{ tabbedMessages.length - index }}
	</button>
	<button
	  v-if="!threadOf"
	  type="button"
	  class="btn btn-sm btn-light float-right ms-2 p-0"
	  @click="closeTab(message.uuid)"
	  >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-x" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
	  </svg>
	</button>
      </li>
    </ul>

    <div class="tab-content">
      <div
	v-for="(message, index) in tabbedMessages"
	class="tab-pane fade"
	:class="tabIndex === index ? 'show active' : ''"
	:id="'tab-' + message.uuid"
	role="tabpanel"
	>
	<div v-if="!threadOf">
	  <button
	    type="button"
	    class="btn btn-sm btn-primary m-2"
	    @click="focusOnThread(message.uuid)"
	    >
	    Focus on this message's thread
	  </button>
	</div>
	<message-content
	  :message="message"
	  :tags="tags"
	  :accountSelected="accountSelected"
	  class="m-2 mb-4">
	</message-content>
      </div>
    </div>

  </div>
</div>
</template>


<script>
import { Modal } from 'bootstrap'
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
	    messages: [],
	    perPage: 8,
	    perPageOptions: [ 8, 16, 32 ],
	    currentPage: 1,
	    totalRows: 1,
	    lastFetched: null,
	    lastLoaded: null,
	    loadError: false,
	    filter: null,
	    filterOn: [],
	    filterOnOptions: [
		{ text: 'From', value: 'from'},
		{ text: 'Recipients', value: 'recipients'},
		{ text: 'Subject', value: 'subject'},
		{ text: 'Body', value: 'body'},
		{ text: 'Attachment', value: 'attachment'},
	    ],
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
	    tags: null,
	    tagsRequired: [],
	    resumeDraftModal: null
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
	// showManageTagsModal () {
	//     this.$bvModal.show('modal-manage-tags')
	// },
	showReworkDraftModal (draftmsg) {
	    this.draftMessageSelected = draftmsg
	    this.resumeDraftModal.show()
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
	fetchMessages () {
	    if (!this.accountSelected) {
		this.messages = []
	    }
	    else {
		var params = '?account=' + this.accountSelected.email
		// Our API uses limit/offset pagination
		params += '&limit=' + this.perPage + '&offset=' + this.perPage * (this.currentPage - 1)
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

		var now = new Date()

		fetch('/mail/api/stored_messages' + params)
		    .then(stream => stream.json())
		    .then(data => {
			this.lastLoaded = now.toISOString()
			this.loadError = false
			this.messages = data.results
			this.totalRows = data.results.length
			if (this.threadOf) {
			    this.tabbedMessages = this.messages
			}
		    }).catch(error => {
			this.lastFetched = now.toISOString()
			this.loadError = true
			console.error(error)
		    })
	    }
	    this.fetchQueued()
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
	this.fetchMessages()

	// To move to non-BootstrapVue JS
	// this.$root.$on('bv::modal::hide', (bvEvent, modalId) => {
	//     if (bvEvent.componentId === 'modal-newdraft' ||
	// 	bvEvent.componentId === 'modal-resumedraft' ||
	// 	bvEvent.componentId === 'modal-reply' ||
	// 	bvEvent.componentId === 'modal-forward') {
	// 	this.fetchDrafts()
	//     }
	// })
 	this.fetchMessagesInterval = setInterval(this.fetchMessages, this.refreshMinutes * 60000)

	this.resumeDraftModal = new Modal(document.getElementById('modal-resumedraft'))

    },
    beforeDestroy() {
    	clearInterval(this.refreshInterval)
	clearInterval(this.fetchMessagesInterval)
    },
    watch: {
	accountSelected: function () {
	    this.tabbedMessages = []
	    this.fetchMessages()
	},
	threadOf: function () {
	    if (this.threadOf == null) {
		this.flowDirection = this.flowDirectionLastNotNull
	    }
	    else {
		this.flowDirectionLastNotNull = this.flowDirection
		this.flowDirection = null
	    }
	    this.fetchMessages()
	},
	timePeriod: function () {
	    this.fetchMessages()
	},
	currentPage: function () {
	    this.fetchMessages()
	},
	filter: function () {
	    this.fetchMessages()
	},
	filterOn: function () {
	    this.fetchMessages()
	},
	flowDirection: function () {
	    if (this.flowDirection != null) {
		this.flowDirectionLastNotNull = this.flowDirection
	    }
	    this.fetchMessages()
	},
	perPage: function () {
	    this.fetchMessages()
	},
	readStatus: function () {
	    this.fetchMessages()
	},
	refreshMinutes: function () {
	    clearInterval(this.fetchMessagesInterval)
	    this.fetchMessagesInterval = setInterval(this.fetchMessages, this.refreshMinutes * 60000)
	},
	tabbedMessages: function () {
	    if (this.threadOf) {
		this.tabIndex = this.indexInTabbedMessages(this.threadOf)
	    }
	},
	tagsRequired: function () {
	    this.fetchMessages()
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
