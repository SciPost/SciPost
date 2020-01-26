<template>
<div>
  <h1>Compose email message</h1>
  <b-form>
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
    <b-button type="savedraft" variant="warning">Save draft</b-button>
    <b-button type="send" variant="success">Send</b-button>
  </b-form>
</div>
</template>

<script>
  export default {
      name: "message-composer",
      props: {
	  originalmessage: {
	      type: Object,
	      required: false,
	  }
      },
      data () {
	  return {
	      form: {
		  torecipient: '',
		  body: '',
	      }
	  }
      },
      mounted () {
      	  if (this.originalmessage) {
      	      this.form.torecipient = this.originalmessage.data.from
      	      this.form.body = '<blockquote>\n' + this.originalmessage.data["body-plain"] + '\n</blockquote>'
      	  }
      }
  }
</script>
