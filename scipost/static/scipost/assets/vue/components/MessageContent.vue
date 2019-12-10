<template>
<div>
  <b-card header-tag="header" footer-tag="footer">
    <template v-slot:header>
      <div class="text-dark">
	On: {{ message.datetimestamp }}
	<br>
	Subject: <strong>{{ message.data.subject }}</strong>
	<br>
	From: {{ message.data.from }}
	<br>
	Recipients: {{ message.data.recipients }}
      </div>
    </template>
    <b-card-text>
      <span v-html="sanitized_html"></span>
    </b-card-text>
    <template v-slot:footer>
      <div class="text-dark">
	<b-button v-b-toggle="'message-json'" class="px-2 py-0">
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
