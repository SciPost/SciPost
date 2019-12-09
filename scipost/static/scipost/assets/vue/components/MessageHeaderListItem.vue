<template>
  <b-list-group-item :id="'item' + [[ message.uuid ]]">
    On {{ message.data.Date }}, from {{ message.data.from }}
  </b-list-group-item>
</template>

<script>
export default {
    name: "message-header-list-item",
    props: {
	message: {
	  type: Object,
	  required: true
	}
    }
}
</script>
