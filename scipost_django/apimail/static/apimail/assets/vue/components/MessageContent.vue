<template>
<div>
  <b-card
    border-variant="primary"
    class="overflow-x-auto"
    header-tag="header"
    footer-tag="footer"
    >
    <template v-slot:header>

      <ul class="list-inline m-2">
	<li class="list-inline-item">
	  <button
	    type="button"
	    class="btn btn-primary"
	    data-bs-toggle="modal"
	    :data-bs-target="'#modal-reply-' + message.uuid"
	    >
	    Reply
	  </button>
	  <div
	    class="modal fade"
	    :id="'modal-reply-' + message.uuid"
	    >
	    <div class="modal-dialog modal-xl">
	      <div class="modal-content">
		<div class="modal-header">
		  <h1 class="modal-title">
		    Reply
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
		    :originalmessage="message"
		    action="reply"
		    :accountSelected="accountSelected"
		    ></message-composer>
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
	</li>
	<li class="list-inline-item">
	  <button
	    type="button"
	    class="btn btn-dark"
	    data-bs-toggle="modal"
	    :data-bs-target="'#modal-forward-' + message.uuid"
	    >
	    Forward
	  </button>
	  <div
	    class="modal fade"
	    :id="'modal-forward-' + message.uuid"
	    >
	    <div class="modal-dialog modal-xl">
	      <div class="modal-content">
		<div class="modal-header">
		  <h1 class="modal-title">
		    Forward
		  </h1>
		</div>
		<div class="modal-body">
		  <message-composer
		    :originalmessage="message"
		    action="forward"
		    :accountSelected="accountSelected"
		    ></message-composer>
		</div>
		<div class="modal-footer">
		  <button
		    type="button"
		    class="btn btn-danger px-2 py-1"
		    data-bs-dismiss="modal"
		    >
		    Close
		  </button>
		</div>
	      </div>
	    </div>
	  </div>
	</li>
	<li class="list-inline-item float-right">
	  <ul class="list-inline">
	    <li class="list-inline-item m-0" v-for="tag in message.tags">
	      <button
		type="button"
		class="btn btn-sm p-1"
		@click.shift="tagMessage(message, tag, 'remove')"
		:style="'background-color: ' + tag.bg_color"
		>
		<small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
	      </button>
	    </li>
	    <li class="list-inline-item float-right mx-2">
	      <button
		type="button"
		class="btn btn-sm btn-secondary"
		data-bs-toggle="modal"
		:data-bs-target="'#modal-tags' + message.uuid"
		>
		Add&nbsp;tag
	      </button>
	      <br><small class="text-muted">Shift-click on tag to remove it</small>
	      <div
		class="modal fade"
		:id="'modal-tags' + message.uuid"
		>
		<div class="modal-dialog">
		  <div class="modal-content">
		    <div class="modal-header">
		      <h1 class="modal-title">
			Add tag(s):
		      </h1>
		    </div>
		    <div class="modal-body">
		      <ul class="list-unstyled">
			<li v-for="tag in tags" class="m-1">
			  <button
			    type="button"
			    class="btn btn-sm p-1"
			    @click="tagMessage(message, tag, 'add')"
			    :style="'background-color: ' + tag.bg_color"
			    >
			    <small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
			  </button>
			</li>
		      </ul>
		    </div>
		    <div class="modal-footer">
		      <button
			type="button"
			class="btn btn-danger px-2 py-1"
			data-bs-dismiss="modal"
			>
			Close
		      </button>
		    </div>
		  </div>
		</div>
	      </div>
	    </li>
	  </ul>
	</li>
      </ul>
      <hr>
      <div class="text-dark">
	<b-row>
	  <b-col class="col-lg-10">
	    On: {{ message.datetimestamp }}
	    <br>
	    Subject: <strong>{{ message.data.subject }}</strong>
	    <br>
	    From: {{ message.data.from }}
	    <br>
	    Recipients: {{ message.data.recipients }}
	  </b-col>
	  <b-col class="col-lg-2">
	    <button
	      type="button"
	      class="btn btn-secondary"
	      data-bs-toggle="modal"
	      :data-bs-target="'#message-events-modal' + message.uuid"
	      >
	      <small>View all events</small>
	    </button>
	    <div
	      class="modal fade"
	      :id="'message-events-modal' + message.uuid"
	      >
	      <div class="modal-dialog">
		<div class="modal-content">
		  <div class="modal-header">
		    <h1 class="modal-title">
		      Events
		    </h1>
		  </div>
		  <div class="modal-body">
		    <ul class="list-unstyled">
	    	      <li v-for="event in message.event_set">
	    		<small>
	    		  {{ event.data.timestamp|toDatestring }}&emsp;{{ event.data.event }}
	    		  <span v-if="event.data.recipient">&emsp;
	    		    [{{ event.data.recipient }}]</span>
	    		</small>
	    	      </li>
		    </ul>
		  </div>
		  <div class="modal-footer">
		    <button
		      type="button"
		      class="btn btn-danger px-2 py-1"
		      data-bs-dismiss="modal"
		      >
		      Close
		    </button>
		  </div>
		</div>
	      </div>
	    </div>
	  </b-col>
	</b-row>
      </div>
    </template>
    <b-card-text>
      <span v-html="sanitized_html"></span>
    </b-card-text>
    <template v-slot:footer>
      <div class="text-dark">
	<div v-if="message.attachment_files.length > 0">
	  <h3>Attachments:</h3>
	  <ul>
	    <li v-for="att in message.attachment_files">
	      <a :href="att.link" target="_blank" class="text-primary">{{ att.data.name }}</a>
	      &emsp;{{ att.data["content-type"] }}&nbsp;({{ att.data.size }} b)
	    </li>
	  </ul>
	</div>
	<button
	  type="button"
	  class="btn mt-2 px-2 py-0"
	  data-bs-toggle="collapse"
	  :data-bs-target="'#message-json' + message.uuid"
	  >
	  <small>View message JSON</small>
	</button>
	<div
	  class="collapse m-2"
	  :id="'message-json' + message.uuid"
	  >
	  {{ message }}
	</div>
      </div>
    </template>
  </b-card>
</div>
</template>

<script>
import Cookies from 'js-cookie'

import MessageComposer from './MessageComposer.vue'

var csrftoken = Cookies.get('csrftoken');

export default {
    name: "message-content",
    components: {
    	MessageComposer,
    },
    props: {
	accountSelected: {
	    type: Object,
	    required: true,
	},
	message: {
	    type: Object,
	    required: true
	},
	tags: {
	    type: Array,
	    required: false
	},
    },
    computed: {
	sanitized_html() {
	    if (this.message.data["body-html"]) {
		return this.$sanitize(this.message.data["body-html"])
	    }
	    return this.$sanitize(this.message.data["body-plain"])
	}
    },
    filters: {
	toDatestring(unixtimestamp) {
	    return new Date(1000 * unixtimestamp).toISOString()
	}
    },
    methods: {
	markAsRead () {
	    if (!this.message.read) {
		fetch('/mail/api/stored_message/' + this.message.uuid + '/mark_as_read',
		      {
			  method: 'PATCH',
			  headers: {
			      "X-CSRFToken": csrftoken,
			  }
		      }
		     ).then(function(response) {
			 if (!response.ok) {
			     throw new Error('HTTP error, status = ' + response.status);
			 }
		     })
		    .catch(error => console.error(error))
		this.message.read = true
	    }
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
		 })
	    	.catch(error => console.error(error))

	    if (action == 'add') {
		// Prevent doubling by removing first, then (re)adding
		message.tags = message.tags.filter(function (item) { return item.pk !== tag.pk })
		message.tags.push(tag)
	    }
	    else if (action == 'remove') {
		message.tags.splice(message.tags.indexOf(tag), 1)
	    }
	},
    },
    mounted () {
	this.markAsRead()
    },
    updated () {
	// needed: mounted is called for leftmost tab in MessagesTable before any data is loaded
	this.markAsRead()
    }
}
</script>
