<template>
  <div>
    {{ message.data["stripped-html"] }}
  </div>
</template>

<script>
  export default {
      name: "message-content",
      props: {
	  message: {
	      type: Object,
	      required: true
	  }
      }
  }
</script>
