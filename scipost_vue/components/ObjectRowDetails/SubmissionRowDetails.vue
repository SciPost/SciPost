<template>
<div class="row mb-0">
  <div class="col">
    <ul class="list list-unstyled">
      <li>
	<a
	  :href="submission.url"
	  target="_blank"
	  rel="nofollow"
	  >
	  <highlight-text
	    :text="submission.title"
	    :queries="queries"
	    >
	  </highlight-text>
	</a>
      </li>
      <li>
	<highlight-text
	  :text="submission.author_list"
	  :queries="queries"
	  >
	</highlight-text>
      <li>
	<ul class="list-inline">
	  <li class="list-inline-item">
	    <strong>{{ submission.identifier }}</strong>
	  </li>
	  <li class="list-inline-item">
	    <em>Submitted on {{ submission.submission_date }} (this version)</em>
	  </li>
	  <li class="list-inline-item">
	    <button
	      class="btn btn-sm btn-outline-secondary px-1 py-0"
	      type="button"
	      data-bs-toggle="collapse"
	      :data-bs-target="'#abstract-' + submission.identifier.replaceAll('.', '-')"
	      >
	      <em>Toggle abstract</em>
	    </button>
	  </li>
	  <li class="list-inline-item">
	    <div
	      class="collapse m-1"
	      :id="'abstract-' + submission.identifier.replaceAll('.', '-')"
	      >
	      <highlight-text
		:text="submission.abstract"
		:queries="queries"
		>
	      </highlight-text>
	    </div>
	  </li>
	</ul>
      </li>
    </ul>
  </div>
</div>
</template>

<script>
import HighlightText from './../HighlightText.vue'

export default {
    name: "submission-row-details",
    components: {
	HighlightText,
    },
    props: {
        submission: {
            type: Object,
            required: true
        },
	queries: {
	    type: Array,
	    required: false
	}
    },
}
</script>
