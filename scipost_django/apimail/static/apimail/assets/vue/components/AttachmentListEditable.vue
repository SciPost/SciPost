<template>
  <div class="row">
    <div class="col col-lg-6">
      <b-form-file
	v-model="newAttachment"
	placeholder="Select a file, or drop it here"
	drop-placeholder="Drop file here"
	>
      </b-form-file>
      <div v-if="newAttachment">
	<button
	  class="btn btn-secondary m-1 p-1"
	  @click="addNewAttachment"
	  >
	  Upload this attachment and add it to your message
	</button>
      </div>
    </div>
    <div class="col col-lg-6">
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
    </div>
  </div>
</template>

<script>
import Cookies from 'js-cookie'

import AttachmentListItem from './AttachmentListItem.vue'

var csrftoken = Cookies.get('csrftoken');

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
		  let formData = new FormData();
		  formData.append('data', JSON.stringify({
		      'size': this.newAttachment.size,
		      'name': this.newAttachment.name,
		      'content-type': this.newAttachment.type,
		      'url': null
		  }))
		  formData.append('file', this.newAttachment)
		  fetch('/mail/api/attachment_file/create',
			{
			    method: 'POST',
			    headers: {
				"X-CSRFToken": csrftoken,
			    },
			    body: formData
			})
		      .then(response => response.json())
		      .then(data => {
			  this.attachments.push(data)
			  this.newAttachment = null
		      })
		      .catch(error => console.error(error))
	      }
	  }
      },
  }

</script>
