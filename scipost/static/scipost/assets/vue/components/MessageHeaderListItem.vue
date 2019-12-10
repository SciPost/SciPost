<template>
<b-list-group-item
  class="py-0"
  :id="'item' + [[ message.uuid ]]"
  >
  <b-row>
    <b-col>
      <button class="btn btn-primary p-1" @click="$emit('view', message)">
	View
      </button>
    </b-col>
    <b-col>
      On: {{ message.datetimestamp }}
      <br>
      From: {{ message.data.from }}
    </b-col>
    <b-col>
      Subject: {{ message.data.subject }}
    </b-col>
  </b-row>
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
