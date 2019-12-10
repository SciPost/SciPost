<template>
<b-list-group-item :id="'item' + [[ message.uuid ]]" class="py-0">
  <b-row>
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
