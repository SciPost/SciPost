<template>
  <div>
    <h1>Vue Search</h1>
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
	    v-for="publication in publicationslist"
	    :key="publication.doi"
	    >
	    {{ publication.doi }}
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
export default {
    name: "search",
    data() {
	return {
	    publicationslist: [],
	}
    },
    methods: {
	fetchPublications () {
	    fetch('/api/journals/publications')
		.then(stream => stream.json())
		.then(data => this.publicationslist = data.results)
		.catch(error => console.error(error))
	},
    },
    mounted() {
	this.fetchPublications()
    },
}
</script>
