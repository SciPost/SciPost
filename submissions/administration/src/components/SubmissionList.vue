<template>
  <div id="todolist">
    <ul>
      <li v-for="submission in submissions">
        <summary v-bind:submission="submission" v-bind:submission="submission.id">
        </summary>
      </li>
    </ul>
  </div>
</template>

<script>
import Summary from './Summary.vue'

export default {
  components: {
    Summary
  },
  // getSubmissions: function () {
  //   this.$http.get('/submissions/api/admin/?format=json').then(function (response) {
  //     console.log(response)
  //     this.submissions = response.data
  //   },
  //   function (response) {
  //     console.log(response)
  //   })
  // },
  // methods: {
  //
  // },
  data: function () {
    return {
      submissions: [
        { text: 'Learn Vue' },
        { text: 'Do hard things' }
      ]
    }
  },
  ready: function () {
    // getSubmissions: function () {
    console.log(this)
    this.$http.get('/submissions/api/admin/?format=json').then(function (response) {
      console.log(response)
      this.submissions = response.data
    },
    function (response) {
      console.log(response)
    //   })
    })
  }
}
</script>
