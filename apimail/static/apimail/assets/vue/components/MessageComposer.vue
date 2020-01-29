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
	    v-model="form.torecipient"
	    type="email"
	    required
	    placeholder="Enter main recipient's email"
	    >
	  </b-form-input>
	</b-form-group>
      </b-col>
    </b-row>
    <b-form-group
      id="cc"
      label="cc:"
      label-for="input-cc"
      class="mb-2"
      >
      <b-form-input
	id="input-cc"
	v-model="form.cc"
	type="email"
	>
      </b-form-input>
    </b-form-group>
    <b-form-group
      id="bcc"
      label="bcc:"
      label-for="input-bcc"
      class="mb-4"
      >
      <b-form-input
	id="input-bcc"
	v-model="form.bcc"
	type="email"
	>
      </b-form-input>
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
    <b-button type="savedraft" variant="warning" @click.stop.prevent="saveDraft">
      Save draft
    </b-button>
    <b-button type="send" variant="success">Send</b-button>
    <template v-if="saveDraftSuccessful">
      <p class="m-2 p-2 bg-success text-white">
	The message draft was successfully saved.
      </p>
    </template>
    <template v-else-if="saveDraftSuccessful === false">
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

var csrftoken = Cookies.get('csrftoken');

export default {
    name: "message-composer",
    props: {
	originalmessage: {
	    type: Object,
	    required: false,
	},
	action: {
	    type: String,
	    required: true,
	},
    },
    data () {
	return {
	    form: {
		from_account: null,
		torecipient: '',
		cc: '',
		bcc: '',
		subject: '',
		body: '',
		sanitized_body_html: '',
	    },
	    from_account_accesses: [],
	    response: null,
	    response_body_json: null,
	    saveDraftSuccessful: null,
	    draftLastSaved: null,
	}
    },
    computed: {
	sanitized_body_html() {
	    return this.$sanitize(this.form.body)
	}
    },
    methods: {
	fetchCurrentAccounts () {
	    fetch('/mail/api/user_account_accesses?current&cansend')
		.then(stream => stream.json())
		.then(data => this.from_account_accesses = data.results)
		.catch(error => console.error(error))
	},
	saveDraft () {
	    fetch('/mail/api/composed_message/create',
	    	  {
	    	      method: 'POST',
	    	      headers: {
	    		  "X-CSRFToken": csrftoken,
	    		  "Content-Type": "application/json; charset=utf-8"
	    	      },
	    	      body: JSON.stringify({
			  'from_account': this.form.from_account,
			  'to_recipient': this.form.torecipient,
			  // 'cc_recipients': this.form.cc,
			  // 'bcc_recipients': this.form.bcc,
			  'subject': this.form.subject,
			  'body_text': this.form.body,
			  'body_html': this.form.sanitized_body_html,
	    	      })
	    	  })
		.then(response => {
		    this.response = response.clone()
		    if (response.ok) {
			this.saveDraftSuccessful = true
		 	this.draftLastSaved = Date().toString()
		    }
	    	    if (!response.ok) {
			this.saveDraftSuccessful = false
	    	    	// throw new Error('HTTP error, status = ' + response.status);
	    	    }
		    return response.json()
	    	})
		.then(responsejson => this.response_body_json = responsejson)
		.catch(error => console.error(error))
	}
    },
    mounted () {
	this.fetchCurrentAccounts()
      	if (this.originalmessage) {
	    this.form.from_account = this.originalmessage.data.To
      	    this.form.body = ('\n\n<blockquote>\n')
	    if (this.action == 'reply') {
      		this.form.torecipient = this.originalmessage.data.sender
		this.form.cc = this.originalmessage.data.recipients
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
    }
}
</script>

<style scoped>

.white-space-pre-wrap {
    white-space: pre-wrap;
}

</style>
