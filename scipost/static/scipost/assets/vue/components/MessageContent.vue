<template>
  <div>
    <h3>Message content:</h3>
    <span v-html="sanitized_html"></span>
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
