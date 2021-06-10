<template>
<div class="m-0 p-0">
  <div v-if="object_type == 'publication'">
    <publication-row-details
      :publication="object"
      >
    </publication-row-details>
  </div>
  <div v-if="object_type == 'submission'">
    <submission-row-details
      :submission="object"
      >
    </submission-row-details>
  </div>
</div>
</template>

<script>
import PublicationRowDetails from './PublicationRowDetails.vue'
import SubmissionRowDetails from './SubmissionRowDetails.vue'

export default {
    name: "object-row-details",
    components: {
        PublicationRowDetails,
	SubmissionRowDetails
    },
    props: {
        object_type: {
            type: String,
            required: true
        },
        object: {
            type: Object,
            required: true
        }
    }
}
</script>
