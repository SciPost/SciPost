<template>
<div>
  <b-card header-tag="header" footer-tag="footer">
    <template v-slot:header>
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
	<div v-if="message.attachments">
	  <h3>Attachments:</h3>
	  <ul>
	    <li v-for="att in message.attachments">
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
  }
</script>
