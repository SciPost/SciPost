<template>
<div>
  <h1 class="mb-4">Compose email message</h1>
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
      label="Attachments:"
      class="mb-4"
      >
      <attachment-list-editable
	:attachments="form.attachments">
      </attachment-list-editable>
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

    <editor-menu-bar :editor="editor" v-slot="{ commands, isActive }">
      <div class="menubar">
        <b-button
	  v-b-tooltip.hover title="boldface"
          :pressed.sync="isActive.bold()"
          @click.stop.prevent="commands.bold"
          >
	  <i class="fa fa-bold"></i>
	</b-button>
        <b-button
	  v-b-tooltip.hover title="italics"
          :pressed.sync="isActive.italic()"
          @click.stop.prevent="commands.italic"
          >
	  <i class="fa fa-italic"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="strikethrough"
          :pressed.sync="isActive.strike()"
          @click.stop.prevent="commands.strike"
          >
	  <i class="fa fa-strikethrough"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="underline"
          :pressed.sync="isActive.underline()"
          @click.stop.prevent="commands.underline"
          >
	  <i class="fa fa-underline"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="inline code"
          :pressed.sync="isActive.code()"
          @click.stop.prevent="commands.code"
          >
          <i class="fa fa-code"></i>
        </b-button>
	<b-button
          class="menubar__b-button"
	  v-b-tooltip.hover title="paragraph"
          :pressed.sync="isActive.paragraph()"
          @click.stop.prevent="commands.paragraph"
          >
          <i class="fa fa-paragraph"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="level 1 heading"
          :pressed.sync="isActive.heading({ level: 1 })"
          @click.stop.prevent="commands.heading({ level: 1 })"
          >
          H1
        </b-button>
        <b-button
	  v-b-tooltip.hover title="level 2 heading"
          :pressed.sync="isActive.heading({ level: 2 })"
          @click.stop.prevent="commands.heading({ level: 2 })"
          >
          H2
        </b-button>
        <b-button
	  v-b-tooltip.hover title="level 3 heading"
          :pressed.sync="isActive.heading({ level: 3 })"
          @click.stop.prevent="commands.heading({ level: 3 })"
          >
          H3
        </b-button>
        <b-button
	  v-b-tooltip.hover title="bulleted list"
          :pressed.sync="isActive.bullet_list()"
          @click.stop.prevent="commands.bullet_list"
          >
          <i class="fa fa-list-ul"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="numbered list"
          :pressed.sync="isActive.ordered_list()"
          @click.stop.prevent="commands.ordered_list"
          >
          <i class="fa fa-list-ol"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="blockquote"
          :pressed.sync="isActive.blockquote()"
          @click.stop.prevent="commands.blockquote"
          >
          <i class="fa fa-quote-right"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="code block"
          :pressed.sync="isActive.code_block()"
          @click.stop.prevent="commands.code_block"
          >
          <i class="fa fa-code"></i> block
        </b-button>
        <b-button
	  v-b-tooltip.hover title="horizontal rule"
	  @click.stop.prevent="commands.horizontal_rule">
	  hr
        </b-button>
        <b-button
	  v-b-tooltip.hover title="undo"
	  @click.stop.prevent="commands.undo">
          <i class="fa fa-undo"></i>
        </b-button>
        <b-button
	  v-b-tooltip.hover title="redo"
	  @click.stop.prevent="commands.redo">
          <i class="fa fa-repeat"></i>
        </b-button>
      </div>
    </editor-menu-bar>
    <editor-content class="editor__content m-1 p-1" :editor="editor" />

    <template v-if="!markReadySuccessful" class="mt-4">
      <b-button
	type="savedraft"
	class="text-white px-1 py-0"
	variant="warning"
	@click.stop.prevent="saveMessage('draft')"
	>
	Save draft
      </b-button>
      <b-button
	type="send"
	class="text-white px-1 py-0"
	variant="primary"
	@click.stop.prevent="saveMessage('ready')"
	>
	Send
      </b-button>
    </template>
    <template v-if="saveDraftSuccessful">
      <p class="m-2 p-2 bg-success text-white">
	The message draft was successfully saved.
      </p>
    </template>
    <template v-else-if="markReadySuccessful">
      <p class="m-2 p-2 bg-success text-white">
	The message was successfully queued for sending.
      </p>
    </template>
    <template v-else-if="saveDraftSuccessful === false || markReadySuccessful === false">
      <p class="m-2 p-2 bg-danger text-white">
	The server responded with an error, please check and try again.<br>
	{{ response_body_json }}
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

import { Editor, EditorContent, EditorMenuBar } from 'tiptap'
import {
    Blockquote,
    CodeBlock,
    HardBreak,
    Heading,
    HorizontalRule,
    OrderedList,
    BulletList,
    ListItem,
    TodoItem,
    TodoList,
    Bold,
    Code,
    Italic,
    Link,
    Strike,
    Underline,
    History,
} from 'tiptap-extensions'

export default {
    name: "message-composer",
    components: {
	AttachmentListEditable,
	EmailListEditable,
	EditorMenuBar, EditorContent,
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
	accountSelected: {
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
		body_html: '',
		attachments: [],
	    },
	    from_account_accesses: [],
	    response: null,
	    response_body_json: null,
	    saveDraftSuccessful: null,
	    draftLastSaved: null,
	    markReadySuccessful: null,
	    editor: new Editor({
		extensions: [
		    new Blockquote(),
		    new BulletList(),
		    new CodeBlock(),
		    new HardBreak(),
		    new Heading({ levels: [1, 2, 3] }),
		    new HorizontalRule(),
		    new ListItem(),
		    new OrderedList(),
		    new TodoItem(),
		    new TodoList(),
		    new Link(),
		    new Bold(),
		    new Code(),
		    new Italic(),
		    new Strike(),
		    new Underline(),
		    new History(),
		],
		content: ''
	    }),
	}
    },
    computed: {
	sanitized_body_html() {
	    return this.$sanitize(this.editor.getHTML())
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
	    var attachment_uuids = []
	    this.form.attachments.forEach( function(att) {
		attachment_uuids.push(att.uuid)
	    })
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
			  'body_text': this.form.body_html, // TODO: remove; only html emails
			  'body_html': this.sanitized_body_html,
			  'attachment_uuids': attachment_uuids
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
	    this.form.body_html = this.draftmessage.body_html
	    this.form.attachments = this.draftmessage.attachment_files
	}
      	else if (this.originalmessage) {
	    this.form.from_account = this.accountSelected.pk
      	    this.form.body_html = ('<br><br><blockquote>')
	    if (this.action == 'reply') {
      		this.form.to_recipient = this.originalmessage.data.sender
		this.form.cc_recipients = this.originalmessage.data.recipients.split(',')
		this.form.subject = 'Re: ' + this.originalmessage.data.subject
		this.form.body_html += ('<p>On ' + this.originalmessage.datetimestamp +
				   ', ' + this.originalmessage.data.from +
				   ' wrote:</p>')
	    }
	    if (this.action == 'forward') {
		this.form.subject = 'Fwd: ' + this.originalmessage.data.subject
		this.form.body_html += ('<p>Begin forwarded message:' +
				   '<br>From: ' + this.originalmessage.data.sender +
				   '<br>Subject: ' + this.originalmessage.subject +
				   '<br>Date: ' + this.originalmessage.datetimestamp +
				   '<br>To: ' + this.originalmessage.data.To +
				   '</p>')
		this.form.attachments = this.originalmessage.attachment_files
	    }
	    if (this.originalmessage.data.hasOwnProperty("body-html")) {
		this.form.body_html += (this.$sanitize(this.originalmessage.data["body-html"]))
	    }
	    else {
		this.form.body_html += (this.$sanitize(this.originalmessage.data["body-plain"]))
	    }
	    this.form.body_html += '</blockquote>'
      	}
	else {
	    // Fill with a couple of blank lines to debug prosemirror
	    this.form.body_html = '<br><br>'
	}
	this.editor.setContent(this.form.body_html)
    },
    beforeDestroy() {
	this.editor.destroy()
    },
}
</script>

<style scoped>

.white-space-pre-wrap {
    white-space: pre-wrap;
}

div.menubar {
    margin: 1px;
    padding: 1px;
}

div.editor__content {
    border: 1px solid black;
}

button.active {
    border-color: black !important;
    border: 3px solid black;
}

</style>
