<template>
<div class="row mb-0">
  <div class="col">
    <ul class="list list-unstyled">
      <li>
	<a
	  :href="publication.url"
	  target="_blank"
	  rel="nofollow"
	  >
	  <highlight-text
	    :text="publication.title"
	    :queries="queries"
	    >
	  </highlight-text>
	</a>
      </li>
      <li>
	<highlight-text
	  :text="publication.author_list"
	  :queries="queries"
	  >
	</highlight-text>
      </li>
      <li>
	<ul class="list-inline">
	  <li class="list-inline-item">
	    <strong>{{ publication.doi_label }}</strong>
	  </li>
	  <li class="list-inline-item">
	    <em>Published on {{ publication.publication_date }}</em>
	  </li>
	  <li class="list-inline-item">
	    <button
	      class="btn btn-sm btn-outline-secondary px-1 py-0"
	      type="button"
	      data-bs-toggle="collapse"
	      :data-bs-target="'#abstract-' + publication.doi_label.replaceAll('.', '-')"
	      >
	      <em>Toggle abstract</em>
	    </button>
	  </li>
	  <li class="list-inline-item">
	    <div
	      class="collapse m-1"
	      :id="'abstract-' + publication.doi_label.replaceAll('.', '-')"
	      >
	      <highlight-text
		:text="publication.abstract"
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
    name: "publication-row-details",
    components: {
	HighlightText,
    },
    props: {
        publication: {
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
