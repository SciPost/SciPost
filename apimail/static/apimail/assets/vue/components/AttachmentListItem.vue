<template>
  <li>
    {{ attachment.name }}&emsp;({{ attachment.type}}, {{ attachment.size }} bytes)
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
  type: File,
  required: true,
  }
  },
  }
</script>
