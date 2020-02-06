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
	  <b-button
	    v-b-modal.modal-reply
	    variant="primary"
	    >
	    Reply
	  </b-button>
	  <b-modal
	    id="modal-reply"
	    size="xl"
	    title="Reply"
	    hide-header-close
	    no-close-on-escape
	    no-close-on-backdrop
	    >
	    <message-composer :originalmessage="message" action="reply"></message-composer>
	    <template v-slot:modal-footer="{ close, }">
	      <b-button size="sm" variant="danger" @click="close()">
		Close
	      </b-button>
	    </template>
	  </b-modal>
	</li>
	<li class="list-inline-item">
	  <b-button
	    v-b-modal.modal-forward
	    variant="dark"
	    text-variant="white"
	    >
	    Forward
	  </b-button>
	  <b-modal
	    id="modal-forward"
	    size="xl"
	    title="Forward"
	    hide-header-close
	    no-close-on-escape
	    no-close-on-backdrop
	    >
	    <message-composer :originalmessage="message" action="forward"></message-composer>
	    <template v-slot:modal-footer="{ close, }">
	      <b-button variant="danger" @click="close()">
		Close
	      </b-button>
	    </template>
	  </b-modal>
	</li>
	<li class="list-inline-item">
	</li>
      </ul>
      <hr>
      <div class="text-dark">
	<b-row>
	<b-col class="col-lg-8">
	  On: {{ message.datetimestamp }}
	  <br>
	  Subject: <strong>{{ message.data.subject }}</strong>
	  <br>
	  From: {{ message.data.from }}
	  <br>
	  Recipients: {{ message.data.recipients }}
	</b-col>
	<b-col class="col-lg-4">
	  <h5>Events for this message:</h5>
	  <ul class="list-unstyled">
	    <li v-for="event in message.event_set">
	      {{ event.data.timestamp|toDatestring }}&emsp;{{ event.data.event }}
	    </li>
	  </ul>
	</b-col>
	</b-row>
      </div>
    </template>
    <b-card-text>
      <span v-html="sanitized_html"></span>
    </b-card-text>
    <template v-slot:footer>
      <div class="text-dark">
	<div v-if="message.attachment_files">
	  <h3>Attachments:</h3>
	  <ul>
	    <li v-for="att in message.attachment_files">
	      <a :href="att.link" target="_blank" class="text-primary">{{ att.data.name }}</a>
	      &emsp;{{ att.data["content-type"] }}&nbsp;({{ att.data.size }} b)
	    </li>
	  </ul>
	</div>
	<b-button v-b-toggle="'message-json'" class="mt-2 px-2 py-0">
	  <small>View message JSON</small>
	</b-button>
	<b-collapse id="message-json" class="m-2">
	  {{ message }}
	</b-collapse>
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
	message: {
	    type: Object,
	    required: true
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
    mounted () {
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
		 });
	    this.message.read = true
	}
    }
}
</script>
