<template>
<li>
  <a :href="attachment.file" target="_blank">{{ attachment.data.name }}</a>
  &emsp;({{ content_type }}, {{ attachment.data.size }} bytes)
  <b-button class="bg-danger p-1" size="sm" @click.stop="$emit('remove')">
    <i class="small fa fa-times text-white"></i>
  </b-button>
</li>
</template>

<script>
export default {
    name: "attachment-list-item",
    props: {
	attachment: {
	    type: Object,
	    required: true,
	}
    },
    data () {
	return {
	    content_type: this.attachment.data['content-type']
	}
    }
}
</script>
