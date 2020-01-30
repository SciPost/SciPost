<template>
  <li>
    {{ email }}&emsp;
    <b-button class="bg-danger p-0" size="sm" @click.stop="$emit('remove')"><i class="small fa fa-times text-white"></i></b-button>
  </li>
</template>

<script>
  export default {
      name: "email-list-item",
      props: {
	  email: {
	      type: String,
	      required: true,
	  }
      },
  }
</script>
