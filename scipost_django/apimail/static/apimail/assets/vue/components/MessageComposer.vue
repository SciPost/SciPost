<template>
<div>
  <div class="row">
    <div class="col-lg-6">
      <template v-if="!markReadySuccessful">
	<button
	  class="btn btn-warning text-white mx-1 px-2 py-1"
	  @click.stop.prevent="saveMessage('draft')"
	  :disabled="saveDraftSuccessful"
	  >
	  Save draft
	</button>
	<span v-if="!allEmailsValid">
	  <button
	    class="btn btn-warning text-white mx-1 px-2 py-1"
	    @click.stop.prevent="validateAllEmails()"
	    :disabled="emailValidationHasRun || (!form.to_recipient && form.cc_recipients.length == 0 && form.bcc_recipients == 0)"
	    >
	    Validate emails
	  </button>
	</span>
	<span v-else>
	  <button
	    class="btn btn-success text-white mx-1 px-2 py-1"
	    >
	    All emails are validated
	  </button>
	</span>
	<button
	  class="btn btn-primary text-white px-2 py-1 mx-1 my-2"
	  :disabled="!emailValidationHasRun || !allEmailsValid"
	  @click.stop.prevent="saveMessage('ready')"
	  >
	  Send
	</button>
      </template>
      <template v-if="markReadySuccessful">
	<p class="m-2 p-2 bg-success text-white">
	  The message was successfully queued for sending.
	</p>
      </template>
      <template v-else-if="saveDraftSuccessful">
	<p class="m-2 p-2 bg-success text-white">
	  The message draft was successfully saved.
	</p>
      </template>
      <template v-if="!responseOK">
	<div class="bg-danger text-white">
	  <p class="mx-2 mb-0 p-2">
	    The server responded with errors, please check and try again.
	  </p>
	  <ul class="pb-2">
	    <li class="m-2" v-for="(field, error) in response_body_json">
	      {{ error }}:&emsp;{{ field }}
	    </li>
	  </ul>
	</div>
      </template>
      <span v-if="draftLastSaved" size="sm">&emsp;[last saved: {{ draftLastSaved }}]</span>
      <template v-if="emailValidationHasRun && !allEmailsValid">
	<p class="m-2 p-2">
	  <strong class="text-danger">Some email addresses cannot be sent to:</strong>
	  <ul class="mb-1">
	    <li v-for="item in emailValidations">{{ item.address }}&emsp;<span v-if="item.can_send" class="text-success">Can send</span><span v-else><strong class="p-1 bg-danger text-white">Cannot send: {{ item.result }}</strong></span></li>
	  </ul>
	  <strong class="text-danger">Please remove the failing addresses from your message draft.</strong>
	</p>
      </template>
    </div>
    <div class="col-lg-6">
      <span
	class="my-1 p-1 bg-info"
	>Add an email address to your address book</span>
      <b-form
	@submit.prevent="addNewEmailToAddressBook(newEmail, newEmailDescription)"
	>
	<b-input-group>
	  <b-form-input
    	    v-model="newEmail"
	    id="new-email-form"
    	    type="email"
	    placeholder="email"
    	    size="sm"
    	    >
	  </b-form-input>
	  <b-input-group-append>
	    <button type="submit" class="btn btn-sm btn-primary">Add</button>
	  </b-input-group-append>
	</b-input-group>
	<b-input-group>
	  <b-form-input
    	    v-model="newEmailDescription"
	    id="new-email-description"
	    placeholder="description (optional)"
    	    size="sm"
    	    >
	  </b-form-input>
	</b-input-group>
      </b-form>
      <div v-if="addNewEmailResponse">
	<ul class="mb-0">
	  <li>Added:&emsp;{{ addNewEmailResponse.address }}&emsp;<span v-if="addNewEmailResponse.can_send" class="text-success">Can send</span><span v-else><strong class="text-danger">Cannot send: {{ addNewEmailResponse.result }}</strong></span></li>
	</ul>
      </div>
    </div>
  </div>
  <hr>
  <b-form>
    <b-row>
      <b-col class="col-lg-6">
	<b-form-group
	  id="from_account"
	  label="From:"
	  label-for="input-from-account"
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
	  >
	  <ul v-if="form.to_recipient">
	    <li>{{ form.to_recipient }}</li>
	  </ul>
	  <select-from-address-book @selected="onToRecipientSelected"></select-from-address-book>
	</b-form-group>
      </b-col>
    </b-row>
    <b-row>
      <b-col class="col-lg-6">
	<b-form-group
	  id="cc"
	  label="cc:"
	  >
	  <email-list-editable :emails="form.cc_recipients" keyword="cc"></email-list-editable>
	</b-form-group>
      </b-col>
      <b-col class="col-lg-6">
	<b-form-group
	  id="bcc"
	  label="bcc:"
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
        <button
	  data-bs-toggle="tooltip"
	  title="boldface"
          :class="isActive.bold() ? 'active' : ''"
          @click.stop.prevent="commands.bold"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-type-bold" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M8.21 13c2.106 0 3.412-1.087 3.412-2.823 0-1.306-.984-2.283-2.324-2.386v-.055a2.176 2.176 0 0 0 1.852-2.14c0-1.51-1.162-2.46-3.014-2.46H3.843V13H8.21zM5.908 4.674h1.696c.963 0 1.517.451 1.517 1.244 0 .834-.629 1.32-1.73 1.32H5.908V4.673zm0 6.788V8.598h1.73c1.217 0 1.88.492 1.88 1.415 0 .943-.643 1.449-1.832 1.449H5.907z"/>
	  </svg>
	</button>
        <button
	  data-bs-toggle="tooltip"
	  title="italics"
          :class="isActive.italic() ? 'active' : ''"
          @click.stop.prevent="commands.italic"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-type-italic" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M7.991 11.674L9.53 4.455c.123-.595.246-.71 1.347-.807l.11-.52H7.211l-.11.52c1.06.096 1.128.212 1.005.807L6.57 11.674c-.123.595-.246.71-1.346.806l-.11.52h3.774l.11-.52c-1.06-.095-1.129-.211-1.006-.806z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="strikethrough"
          :class="isActive.strike() ? 'active' : ''"
          @click.stop.prevent="commands.strike"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-type-strikethrough" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M8.527 13.164c-2.153 0-3.589-1.107-3.705-2.81h1.23c.144 1.06 1.129 1.703 2.544 1.703 1.34 0 2.31-.705 2.31-1.675 0-.827-.547-1.374-1.914-1.675L8.046 8.5h3.45c.468.437.675.994.675 1.697 0 1.826-1.436 2.967-3.644 2.967zM6.602 6.5H5.167a2.776 2.776 0 0 1-.099-.76c0-1.627 1.436-2.768 3.48-2.768 1.969 0 3.39 1.175 3.445 2.85h-1.23c-.11-1.08-.964-1.743-2.25-1.743-1.23 0-2.18.602-2.18 1.607 0 .31.083.581.27.814z"/>
	    <path fill-rule="evenodd" d="M15 8.5H1v-1h14v1z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="underline"
          :class="isActive.underline() ? 'active' : ''"
          @click.stop.prevent="commands.underline"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-type-underline" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path d="M5.313 3.136h-1.23V9.54c0 2.105 1.47 3.623 3.917 3.623s3.917-1.518 3.917-3.623V3.136h-1.23v6.323c0 1.49-.978 2.57-2.687 2.57-1.709 0-2.687-1.08-2.687-2.57V3.136z"/>
	    <path fill-rule="evenodd" d="M12.5 15h-9v-1h9v1z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="inline code"
          :class="isActive.code() ? 'active' : ''"
          @click.stop.prevent="commands.code"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-code" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M5.854 4.146a.5.5 0 0 1 0 .708L2.707 8l3.147 3.146a.5.5 0 0 1-.708.708l-3.5-3.5a.5.5 0 0 1 0-.708l3.5-3.5a.5.5 0 0 1 .708 0zm4.292 0a.5.5 0 0 0 0 .708L13.293 8l-3.147 3.146a.5.5 0 0 0 .708.708l3.5-3.5a.5.5 0 0 0 0-.708l-3.5-3.5a.5.5 0 0 0-.708 0z"/>
	  </svg>
        </button>
	<button
	  data-bs-toggle="tooltip"
	  title="paragraph"
          :class="isActive.paragraph() ? 'active' : ''"
          @click.stop.prevent="commands.paragraph"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-paragraph" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M8 1h4.5a.5.5 0 0 1 0 1H11v12.5a.5.5 0 0 1-1 0V2H9v12.5a.5.5 0 0 1-1 0V1z"/>
	    <path d="M9 1v8H7a4 4 0 1 1 0-8h2z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="level 1 heading"
          :class="isActive.heading({ level: 1 }) ? 'active' : ''"
          @click.stop.prevent="commands.heading({ level: 1 })"
          >
          H1
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="level 2 heading"
          :class="isActive.heading({ level: 2 }) ? 'active' : ''"
          @click.stop.prevent="commands.heading({ level: 2 })"
          >
          H2
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="level 3 heading"
          :class="isActive.heading({ level: 3 }) ? 'active' : ''"
          @click.stop.prevent="commands.heading({ level: 3 })"
          >
          H3
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="bulleted list"
          :class="isActive.bullet_list() ? 'active' : ''"
          @click.stop.prevent="commands.bullet_list"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-list-ul" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M5 11.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm-3 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="numbered list"
          :class="isActive.ordered_list() ? 'active' : ''"
          @click.stop.prevent="commands.ordered_list"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-list-ol" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M5 11.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5z"/>
	    <path d="M1.713 11.865v-.474H2c.217 0 .363-.137.363-.317 0-.185-.158-.31-.361-.31-.223 0-.367.152-.373.31h-.59c.016-.467.373-.787.986-.787.588-.002.954.291.957.703a.595.595 0 0 1-.492.594v.033a.615.615 0 0 1 .569.631c.003.533-.502.8-1.051.8-.656 0-1-.37-1.008-.794h.582c.008.178.186.306.422.309.254 0 .424-.145.422-.35-.002-.195-.155-.348-.414-.348h-.3zm-.004-4.699h-.604v-.035c0-.408.295-.844.958-.844.583 0 .96.326.96.756 0 .389-.257.617-.476.848l-.537.572v.03h1.054V9H1.143v-.395l.957-.99c.138-.142.293-.304.293-.508 0-.18-.147-.32-.342-.32a.33.33 0 0 0-.342.338v.041zM2.564 5h-.635V2.924h-.031l-.598.42v-.567l.629-.443h.635V5z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="blockquote"
          :class="isActive.blockquote() ? 'active' : ''"
          @click.stop.prevent="commands.blockquote"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-blockquote-left" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M2 3.5a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5zm5 3a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5zm0 3a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5zm-5 3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"/>
	    <path d="M3.734 6.352a6.586 6.586 0 0 0-.445.275 1.94 1.94 0 0 0-.346.299 1.38 1.38 0 0 0-.252.369c-.058.129-.1.295-.123.498h.282c.242 0 .431.06.568.182.14.117.21.29.21.521a.697.697 0 0 1-.187.463c-.12.14-.289.21-.503.21-.336 0-.577-.108-.721-.327C2.072 8.619 2 8.328 2 7.969c0-.254.055-.485.164-.692.11-.21.242-.398.398-.562.16-.168.33-.31.51-.428.18-.117.33-.213.451-.287l.211.352zm2.168 0a6.588 6.588 0 0 0-.445.275 1.94 1.94 0 0 0-.346.299c-.113.12-.199.246-.257.375a1.75 1.75 0 0 0-.118.492h.282c.242 0 .431.06.568.182.14.117.21.29.21.521a.697.697 0 0 1-.187.463c-.12.14-.289.21-.504.21-.335 0-.576-.108-.72-.327-.145-.223-.217-.514-.217-.873 0-.254.055-.485.164-.692.11-.21.242-.398.398-.562.16-.168.33-.31.51-.428.18-.117.33-.213.451-.287l.211.352z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="code block"
          :class="isActive.code_block() ? 'active' : ''"
          @click.stop.prevent="commands.code_block"
          >
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-code" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M5.854 4.146a.5.5 0 0 1 0 .708L2.707 8l3.147 3.146a.5.5 0 0 1-.708.708l-3.5-3.5a.5.5 0 0 1 0-.708l3.5-3.5a.5.5 0 0 1 .708 0zm4.292 0a.5.5 0 0 0 0 .708L13.293 8l-3.147 3.146a.5.5 0 0 0 .708.708l3.5-3.5a.5.5 0 0 0 0-.708l-3.5-3.5a.5.5 0 0 0-.708 0z"/>
	  </svg> block
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="horizontal rule"
	  @click.stop.prevent="commands.horizontal_rule">
	  hr
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="undo"
	  @click.stop.prevent="commands.undo">
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-arrow-counterclockwise" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M8 3a5 5 0 1 1-4.546 2.914.5.5 0 0 0-.908-.417A6 6 0 1 0 8 2v1z"/>
	    <path d="M8 4.466V.534a.25.25 0 0 0-.41-.192L5.23 2.308a.25.25 0 0 0 0 .384l2.36 1.966A.25.25 0 0 0 8 4.466z"/>
	  </svg>
        </button>
        <button
	  data-bs-toggle="tooltip"
	  title="redo"
	  @click.stop.prevent="commands.redo">
	  <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-arrow-clockwise" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
	    <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
	    <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
	  </svg>
        </button>
      </div>
    </editor-menu-bar>
    <editor-content class="editor__content m-1 p-1" :editor="editor" />
  </b-form>
</div>
</template>

<script>
import Cookies from 'js-cookie'

import EmailListEditable from './EmailListEditable.vue'
import AttachmentListEditable from './AttachmentListEditable.vue'
import SelectFromAddressBook from './SelectFromAddressBook.vue'

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
	SelectFromAddressBook
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
		headers_added: {},
		attachments: [],
	    },
	    newEmail: null,
	    newEmailDescription: null,
	    addNewEmailResponse: null,
	    addressOptions: [],
	    emailValidations: [],
	    emailValidationHasRun: false,
	    allEmailsValid: false,
	    from_account_accesses: [],
	    response: null,
	    responseOK: true,
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
	onToRecipientSelected (value) {
	    if (value) this.form.to_recipient = value.address
	},
	onCCRecipientSelected (value) {
	    if (value) this.form.cc_recipients.push(value.address)
	},
	onBCCRecipientSelected (value) {
	    if (value) this.form.cc_recipients.push(value.address)
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
			  'headers_added': this.form.headers_added,
			  'attachment_uuids': attachment_uuids
	    	      })
	    	  })
		.then(response => {
		    this.response = response.clone()
		    if (response.ok) {
			this.responseOK = true
			if (status === 'draft') {
			    this.saveDraftSuccessful = true
		 	    this.draftLastSaved = Date().toString()
			}
			if (status === 'ready') {
			    this.markReadySuccessful = true
			}
		    }
	    	    if (!response.ok) {
			this.responseOK = false
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
	},
	addNewEmailToAddressBook (email, description) {
	    fetch('/mail/api/check_address_book',
	    	  {
	    	      method: 'POST',
	    	      headers: {
	    		  "X-CSRFToken": csrftoken,
	    		  "Content-Type": "application/json; charset=utf-8"
	    	      },
	    	      body: JSON.stringify({
	    		  'email': email,
			  'description': description
	    	      })
		  })
		.then(response => response.json())
		.then(responsejson => this.addNewEmailResponse = responsejson)
		.catch(error => console.error(error))
	    this.newEmail = null
	    this.newEmailDescription = null
	},
	verifyEmailValidity (email) {
	    fetch('/mail/api/check_address_book',
	     	  {
	     	      method: 'POST',
	     	      headers: {
	     		  "X-CSRFToken": csrftoken,
	     		  "Content-Type": "application/json; charset=utf-8"
	     	      },
	     	      body: JSON.stringify({
	     		  'email': email
	     	      })
	     	  })
	     	.then(response => response.json())
		.then(responsejson => this.emailValidations.push(responsejson))
		.catch(error => console.error(error))
	},
	validateAllEmails () {
	    this.emailValidations = []
	    if (this.form.to_recipient) this.verifyEmailValidity(this.form.to_recipient)
	    this.form.cc_recipients.forEach(email => this.verifyEmailValidity(email))
	    this.form.bcc_recipients.forEach(email => this.verifyEmailValidity(email))
	    this.emailValidationHasRun = true
	}
    },
    mounted () {
	this.fetchCurrentAccounts()
    },
    watch: {
	accountSelected: function () {
	    this.form.from_account = this.accountSelected.pk
	    this.form.headers_added['Reply-To'] = this.accountSelected.email
	},
	draftmessage: function () {
	    this.currentdraft_uuid = this.draftmessage.uuid
	    this.form.from_account = this.draftmessage.from_account
	    this.form.to_recipient = this.draftmessage.to_recipient
	    this.form.cc_recipients = this.draftmessage.cc_recipients
	    this.form.bcc_recipients = this.draftmessage.bcc_recipients
	    this.form.subject = this.draftmessage.subject
	    this.form.body_html = this.draftmessage.body_html
	    this.form.attachments = this.draftmessage.attachment_files

	    this.editor.setContent(this.form.body_html)
	},
	originalmessage: function () {
      	    this.form.body_html = ('<br><br><blockquote>')
	    this.form.headers_added['In-Reply-To'] = this.originalmessage.data['Message-Id']
	    if (this.originalmessage.data['References']) {
		this.form.headers_added['References'] = (
		    this.originalmessage.data['References'] + " "
			+ this.originalmessage.data['Message-Id'])
	    }
	    else {
		this.form.headers_added['References'] = this.originalmessage.data['Message-Id']
	    }
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

	    this.editor.setContent(this.form.body_html)
	},
	"form.to_recipient": function () {
	    this.emailValidationHasRun = false
	    this.allEmailsValid = false
	},
	"form.cc_recipients": function () {
	    this.emailValidationHasRun = false
	    this.allEmailsValid = false
	},
	"form.bcc_recipients": function () {
	    this.emailValidationHasRun = false
	    this.allEmailsValid = false
	},
	form: {
	    handler: function () {
		this.saveDraftSuccessful = false
	    },
	    deep: true
	},
	sanitized_body_html: function () { // separate watcher since this is a computed field
	    this.saveDraftSuccessful = false
	},
	newEmail: function () {
	    this.addNewEmailResponse = null
	},
	emailValidations: function () {
	    this.allEmailsValid = true
	    this.emailValidations.forEach(item => {
		if (!item.can_send) this.allEmailsValid = false
	    })
	}
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
