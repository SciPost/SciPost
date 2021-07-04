<template>
<div class="m-0 p-0">
  <div v-if="object_type == 'publication'">
    <publication-row-details
      :publication="object"
      :queries="queries"
      >
    </publication-row-details>
  </div>
  <div v-if="object_type == 'submission'">
    <submission-row-details
      :submission="object"
      :queries="queries"
      >
    </submission-row-details>
  </div>
  <div v-if="object_type == 'subsidy-finadmin'">
    <subsidy-fin-admin-row-details
      :subsidy="object"
      >
    </subsidy-fin-admin-row-details>
  </div>
</div>
</template>

<script>
import PublicationRowDetails from './PublicationRowDetails.vue'
import SubmissionRowDetails from './SubmissionRowDetails.vue'
import SubsidyFinAdminRowDetails from './SubsidyFinAdminRowDetails.vue'

export default {
    name: "object-row-details",
    components: {
        PublicationRowDetails,
	SubmissionRowDetails,
	SubsidyFinAdminRowDetails
    },
    props: {
        object_type: {
            type: String,
            required: true
        },
        object: {
            type: Object,
            required: true
        },
	queries: {
	    type: Array,
	    required: false
	}
    }
}
</script>
