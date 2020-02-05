<template>
<div>
  <h1>Compose email message</h1>
  <b-form>
    <b-row>
      <b-col class="col-lg-6">
	<b-form-group
	  id="from_account"
	  label="From:"
	  label-for="input-from-account-access"
	  class="mb-4"
	  >
	  <b-form-select
	    id="input-from-account"
	    v-model="form.from_account"
	    :options="from_account_accesses"
	    type="int"
	    value-field="account.pk"
	    text-field="account.email"
	    >
	  </b-form-select>
	</b-form-group>
      </b-col>
      <b-col class="col-lg-6">
	<b-form-group
	  id="to-recipient"
	  label="To:"
	  label-for="input-to-recipient"
	  class="mb-4"
	  >
	  <b-form-input
	    id="input-to-recipient"
	    v-model="form.to_recipient"
	    type="email"
	    required
	    placeholder="Enter main recipient's email"
	    >
	  </b-form-input>
	</b-form-group>
      </b-col>
    </b-row>
    <b-row>
      <b-col class="col-lg-6">
	<b-form-group
	  id="cc"
	  label="cc:"
	  class="mb-4"
	  >
	  <email-list-editable :emails="form.cc_recipients" keyword="cc"></email-list-editable>
	</b-form-group>
      </b-col>
      <b-col class="col-lg-6">
	<b-form-group
	  id="bcc"
	  label="bcc:"
	  class="mb-4"
	  >
	  <email-list-editable :emails="form.bcc_recipients" keyword="bcc"></email-list-editable>
	</b-form-group>
      </b-col>
    </b-row>
    <b-form-group
      id="attachments"
      label="attachments:"
      class="mb-4"
      >
      <attachment-list-editable
	:attachments="form.attachments"></attachment-list-editable>
    </b-form-group>
    <b-form-group
      id="subject"
      label="Subject:"
      label-for="input-subject"
      class="mb-4"
      >
      <b-form-input
	id="input-subject"
	v-model="form.subject"
	>
      </b-form-input>
    </b-form-group>
    <b-row>
      <b-col class="col-lg-6">
	<b-form-group
	  id="message-body"
	  label="Message:"
	  label-for="input-message-body"
	  >
	  <b-form-textarea
	    id="input-message-body"
	    v-model="form.body"
	    rows="10"
	    >
	  </b-form-textarea>
	</b-form-group>
      </b-col>
      <b-col class="col-lg-6">
	<h3>Preview:</h3>
	<span
	  v-html="sanitized_body_html"
	  class="white-space-pre-wrap"
	  ></span>
      </b-col>
    </b-row>
    <template v-if="!markReadySuccessful">
      <b-button
	type="savedraft"
	variant="warning"
	@click.stop.prevent="saveMessage('draft')"
	>
	Save draft
      </b-button>
      <b-button
	type="send"
	variant="success"
	@click.stop.prevent="saveMessage('ready')"
	>
	Queue for sending
      </b-button>
    </template>
    <template v-if="saveDraftSuccessful">
      <p class="m-2 p-2 bg-success text-white">
	The message draft was successfully saved.
      </p>
      <p>JSON: {{ response_body_json }}</p>
      <p>Draft: {{ draftmessage }}</p>
    </template>
    <template v-else-if="markReadySuccessful">
      <p class="m-2 p-2 bg-success text-white">
	The message was successfully queued for sending.
      </p>
    </template>
    <template v-else-if="saveDraftSuccessful === false || markReadySuccessful === false">
      <p class="m-2 p-2 bg-danger text-white">
	The server responded with an error, please check and try again
      </p>
    </template>

    <span v-if="draftLastSaved" size="sm">&emsp;[last saved: {{ draftLastSaved }}]</span>

  </b-form>
</div>
</template>

<script>
import Cookies from 'js-cookie'

import EmailListEditable from './EmailListEditable.vue'
import AttachmentListEditable from './AttachmentListEditable.vue'

var csrftoken = Cookies.get('csrftoken');

export default {
    name: "message-composer",
    components: {
	AttachmentListEditable,
	EmailListEditable,
    },
    props: {
	draftmessage: {
	    type: Object,
	    required: false,
	},
	originalmessage: {
	    type: Object,
	    required: false,
	},
	action: {
	    type: String,
	    required: false,
	},
    },
    data () {
	return {
	    currentdraft_uuid: null,
	    form: {
		from_account: null,
		to_recipient: '',
		cc_recipients: [],
		bcc_recipients: [],
		subject: '',
		body: '',
		sanitized_body_html: '',
		attachments: [],
	    },
	    from_account_accesses: [],
	    response: null,
	    response_body_json: null,
	    saveDraftSuccessful: null,
	    draftLastSaved: null,
	    markReadySuccessful: null,
	}
    },
    computed: {
	sanitized_body_html() {
	    return this.$sanitize(this.form.body)
	}
    },
    methods: {
	fetchCurrentAccounts () {
	    fetch('/mail/api/user_account_accesses?current=true&cansend=true')
		.then(stream => stream.json())
		.then(data => this.from_account_accesses = data.results)
		.catch(error => console.error(error))
	},
	saveMessage (status) {
	    var url = '/mail/api/composed_message'
	    var method = 'POST'
	    if (this.currentdraft_uuid) { // draft message exists, update
		url += '/' + this.currentdraft_uuid + '/update'
		method = 'PATCH'
	    }
	    else {
		url += '/create'
	    }
	    fetch(url,
	    	  {
	    	      method: method,
	    	      headers: {
	    		  "X-CSRFToken": csrftoken,
	    		  "Content-Type": "application/json; charset=utf-8"
	    	      },
	    	      body: JSON.stringify({
			  'status': status,
			  'from_account': this.form.from_account,
			  'to_recipient': this.form.to_recipient,
			  'cc_recipients': this.form.cc_recipients,
			  'bcc_recipients': this.form.bcc_recipients,
			  'subject': this.form.subject,
			  'body_text': this.form.body,
			  'body_html': this.form.sanitized_body_html,
			  'attachments': this.form.attachments
	    	      })
	    	  })
		.then(response => {
		    this.response = response.clone()
		    if (response.ok) {
			if (status === 'draft') {
			    this.saveDraftSuccessful = true
		 	    this.draftLastSaved = Date().toString()
			}
			if (status === 'ready') {
			    this.markReadySuccessful = true
			}
		    }
	    	    if (!response.ok) {
			if (status === 'draft') {
			    this.saveDraftSuccessful = false
			}
			if (status === 'ready') {
			    this.markReadySuccessful = false
			}
	    	    }
		    return response.json()
	    	})
		.then(responsejson => {
		    this.response_body_json = responsejson
		    this.currentdraft_uuid = responsejson.uuid
		})
		.catch(error => console.error(error))
	}
    },
    mounted () {
	this.fetchCurrentAccounts()
	if (this.draftmessage) {
	    this.currentdraft_uuid = this.draftmessage.uuid
	    this.form.from_account = this.draftmessage.from_account
	    this.form.to_recipient = this.draftmessage.to_recipient
	    this.form.cc_recipients = this.draftmessage.cc_recipients
	    this.form.bcc_recipients = this.draftmessage.bcc_recipients
	    this.form.subject = this.draftmessage.subject
	    this.form.body = this.draftmessage.body_text
	    this.form.sanitized_body_html = this.$sanitize(this.draftmessage.body_html)
	}
      	else if (this.originalmessage) {
	    this.form.from_account = this.originalmessage.data.To
      	    this.form.body = ('\n\n<blockquote>\n')
	    if (this.action == 'reply') {
      		this.form.to_recipient = this.originalmessage.data.sender
		this.form.cc_recipients = this.originalmessage.data.recipients.split(',')
		this.form.subject = 'Re: ' + this.originalmessage.data.subject
		this.form.body += ('On ' + this.originalmessage.datetimestamp +
				   ', ' + this.originalmessage.data.from +
				   ' wrote:\n\n')
	    }
	    if (this.action == 'forward') {
		this.form.subject = 'Fwd: ' + this.originalmessage.data.subject
		this.form.body += ('Begin forwarded message:\n\n' +
				   'From: ' + this.originalmessage.data.sender +
				   '\nSubject: ' + this.originalmessage.subject +
				   '\nDate: ' + this.originalmessage.datetimestamp +
				   '\nTo: ' + this.originalmessage.data.To +
				   '\n\n')
	    }
	    this.form.body += (this.originalmessage.data["body-plain"] +
			       '\n</blockquote>')
      	}
    },
}
</script>

<style scoped>

.white-space-pre-wrap {
    white-space: pre-wrap;
}

</style>
