<template>
  <li>
    {{ email }}&emsp;
    <b-button class="bg-danger px-1 py-0 text-white" size="sm" @click.stop="$emit('remove')">
      X
    </b-button>
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
