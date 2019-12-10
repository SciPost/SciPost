<template>
<div>
  <b-list-group>
    <message-header-list-item
      v-for="message in apidata.results"
      :message="message"
      :key="message.id"
      @view="viewDetail"
      >
    </message-header-list-item>
  </b-list-group>
  <div>
    {{ selected_message }}
  </div>
</div>
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
