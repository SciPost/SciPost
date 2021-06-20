<template>
  <li>
    {{ email }}&emsp;
    <button
      class="btn btn-sm btn-danger px-1 py-0"
      @click.stop="$emit('remove')">
      X
    </button>
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
