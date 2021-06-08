<template>
  <div>
    <h1>Search</h1>

    <div class="input-group mb-3">
      <span class="input-group-text">Basic</span>
      <input v-model="searchQuery" type="text" class="form-control">
    </div>
    <hr>
    <ul class="nav nav-tabs" id="myTab" role="tablist">
      <li class="nav-item" role="presentation">
	<button class="nav-link active" id="publications-tab" data-bs-toggle="tab" data-bs-target="#publications" type="button" role="tab" aria-controls="publications" aria-selected="true">Publications</button>
      </li>
      <li class="nav-item" role="presentation">
	<button class="nav-link" id="submissions-tab" data-bs-toggle="tab" data-bs-target="#submissions" type="button" role="tab" aria-controls="submissions" aria-selected="false">Submissions</button>
      </li>
    </ul>
    <div class="tab-content" id="myTabContent">
      <div class="tab-pane fade show active" id="publications" role="tabpanel" aria-labelledby="publications-tab">
      	<ul>
	  <li
	    v-for="publication in publications"
	    :key="publication.doi"
	    class="mb-3"
	    >
	    <ul class="list list-unstyled">
	      <li>{{ publication.title }}</li>
	      <li>{{ publication.author_list }}</li>
	      <li>{{ publication.abstract }}</li>
	      <li>{{ publication.doi_label }}</li>
	      <li>{{ publication.url }}</li>
	    </ul>
	  </li>
	</ul>
      </div>
      <div class="tab-pane fade" id="submissions" role="tabpanel" aria-labelledby="submissions-tab">
	Submissions
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from '@vue/composition-api'

var debounce = require('lodash.debounce')

export default {
    name: "search",

    setup() {

	const searchQuery = ref('')

	const publications = ref([])

	const fetching = ref(false)

	const error = ref(null)

	const getPublications = debounce(
	    async () => {
		fetching.value = true
		try {
		    const response = await fetch(`/api/publications?doi_label__icontains=${searchQuery.value}`)
		    const json = await response.json()
		    publications.value = json.results
		} catch (errors) {
		    error.value = errors
		} finally {
		    fetching.value = false
		}
	    },
	    300)

	onMounted(getPublications)

	watch(searchQuery, getPublications)

	return {
	    searchQuery,
	    publications,
	    fetching,
	    error,
	}
    },
}
</script>
