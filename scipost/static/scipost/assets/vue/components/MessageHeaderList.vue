<template>
    <b-list-group>
    <message-header-list-item
	v-for="message in apidata.results"
	v-bind:message="message"
	v-bind:key="message.id"
    ></message-header-list-item>
  </b-list-group>
</template>

<script>
  import MessageHeaderListItem from './MessageHeaderListItem.vue'

  export default {
      name: "message-header-list",
      components: {
	  MessageHeaderListItem,
      },
      data() {
	  return {
	      apidata: [],
	      results: [],
	  }
      },
      created: function () {
	  fetch('/mail/api/stored_messages')
	      .then(stream => stream.json())
	      .then(data => this.apidata = data)
	      .catch(error => console.error(error))
      }
  }
</script>
