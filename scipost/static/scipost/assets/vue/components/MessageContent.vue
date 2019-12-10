<template>
<div>
  <b-card header-tag="header" footer-tag="footer">
    <template v-slot:header>
      <div class="text-dark">
	On: {{ message.datetimestamp }}
	<br>
	From: {{ message.data.from }}
	<br>
	Recipients: {{ message.data.recipients }}
	<br>
	Subject: <strong>{{ message.data.subject }}</strong>
      </div>
    </template>
    <b-card-text>
      <h3>Message content:</h3>
      <span v-html="sanitized_html"></span>
    </b-card-text>
    <template v-slot:footer>
      <div class="text-dark">
	{{ message.uuid }}
      </div>
    </template>
  </b-card>
</div>
</template>

<script>
  export default {
      name: "message-content",
      props: {
	  message: {
	      type: Object,
	      required: true
	  },
      },
      computed: {
	  sanitized_html() {
	      return this.$sanitize(this.message.data["stripped-html"])
	  }
      },
  }
</script>
