<template>
  <b-row>
    <b-col class="col-lg-6">
      <b-form-file
	multiple
	v-model="attachments"
	placeholder="Select a file, or drop it here"
	drop-placeholder="Drop file here"
	>
      </b-form-file>
    </b-col>
    <b-col class="col-lg-6">
      <h3>Attachments:</h3>
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
  }
  }
  }

</script>
