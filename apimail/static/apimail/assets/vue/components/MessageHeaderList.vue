<template>
<div>
  <b-list-group>
    <message-header-list-item
      v-for="message in apidata.results"
      :message="message"
      :key="message.id"
      :class="{'active': (message === selected_message) }"
      @view="viewDetail"
      >
    </message-header-list-item>
  </b-list-group>
  <div v-if="selected_message" class="mt-2">
    <message-content :message="selected_message"></message-content>
  </div>
</div>
</template>

<script>
  import MessageHeaderListItem from './MessageHeaderListItem.vue'
  import MessageContent from './MessageContent.vue'

  export default {
      name: "message-header-list",
      components: {
	  MessageHeaderListItem,
	  MessageContent
      },
      data() {
	  return {
	      apidata: [],
	      results: [],
	      selected_message: null,
	  }
      },
      created: function () {
	  fetch('/mail/api/stored_messages')
	      .then(stream => stream.json())
	      .then(data => this.apidata = data)
	      .catch(error => console.error(error))
      },
      methods: {
	  viewDetail(message) {
	      this.selected_message = message
	  }
      }
  }
</script>
