<template>
  <div id="app">
    <submission-list></submission-list>
    <user-input></user-input>
  </div>
</template>

<script>
import SubmissionList from './components/SubmissionList.vue'
import UserInput from './components/UserInput.vue'

export default {
  components: {
    SubmissionList,
    UserInput
  }
}
</script>
