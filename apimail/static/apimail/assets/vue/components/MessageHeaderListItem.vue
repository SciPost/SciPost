<template>
<b-list-group-item
  :id="'item' + [[ message.uuid ]]"
  >
  <b-row @click="$emit('view', message)" class="m-0">
    <b-col>
      On: {{ message.datetimestamp }}
      <br>
      Subject: {{ message.data.subject }}
    </b-col>
    <b-col>
      From: {{ message.data.from }}
      <br>
      Recipients: {{ message.data.recipients }}
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
