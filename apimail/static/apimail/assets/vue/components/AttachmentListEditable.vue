<template>
  <b-row>
    <b-col class="col-lg-6">
      <b-form-file
	v-model="newAttachment"
	placeholder="Select a file, or drop it here"
	drop-placeholder="Drop file here"
	>
      </b-form-file>
      <div v-if="newAttachment">
	<b-button
	  class="m-1 p-1"
	  variant="secondary"
	  @click="addNewAttachment"
	  >
	  Add this attachment to your message
	</b-button>
      </div>
    </b-col>
    <b-col class="col-lg-6">
      <div v-if="attachments.length > 0">
	<h3>Current attachments to this message:</h3>
	<ul>
	  <li
	    is="attachment-list-item"
	    v-for="(attachment, index) in attachments"
	    :key="'att-' + index"
	    :attachment="attachment"
	    @remove="attachments.splice(index, 1)"
	    >
	  </li>
	</ul>
      </div>
    </b-col>
  </b-row>
</template>

<script>

  import AttachmentListItem from './AttachmentListItem.vue'

  export default {
      name: "attachment-list-editable",
      components: {
	  AttachmentListItem,
      },
      props: {
	  attachments: {
	      type: Array,
	      required: true,
	  },
      },
      data () {
	  return {
	      newAttachment: null
	  }
      },
      methods: {
	  addNewAttachment () {
	      if (this.newAttachment) {
		  this.attachments.push(this.newAttachment)
		  this.newAttachment = null
	      }
	  }
      },
  }

</script>
