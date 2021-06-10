<template>
<div class="row mb-0">
  <div class="col">
    <ul class="list list-unstyled">
      <li>
	<a :href="submission.url" target="_blank" rel="nofollow">{{ submission.title }}</a>
      </li>
      <li>{{ submission.author_list }}</li>
      <li>
	<ul class="list-inline">
	  <li class="list-inline-item">
	    <strong>{{ submission.identifier }}</strong>
	  </li>
	  <li class="list-inline-item"><em>Submitted on {{ submission.submission_date }} (this version)</em></li>
	  <li class="list-inline-item">
	    <button class="btn btn-sm btn-outline-secondary p-0" type="button"
		    data-bs-toggle="collapse" :data-bs-target="'#abstract-' + submission.identifier.replaceAll('.', '-')">
	      <em>Toggle abstract</em>
	    </button>
	  </li>
	  <li class="list-inline-item">
	    <div class="collapse m-1" :id="'abstract-' + submission.identifier.replaceAll('.', '-')">
	      {{ submission.abstract }}
	    </div>
	  </li>
	</ul>
      </li>
    </ul>
  </div>
</div>
</template>

<script>
export default {
    name: "submission-row-details",
    props: {
        submission: {
            type: Object,
            required: true
        }
    },
}
</script>
