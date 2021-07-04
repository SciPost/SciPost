<template>
<div>
  <div class="row mb-4">
    <div class="col-md-3">
      <h1>Search</h1>
      <p>
	<a
	  href="mailto:techsupport@scipost.org"
	  rel="nofollow"
	  >
	  Feedback
	</a>
      </p>
    </div>
    <div class="col-md-9">
      <div
	class="accordion"
	id="searchTipsAccordion"
	>
	<div class="accordion-item">
	  <h2
	    class="accordion-header"
	    id="basicSearchTipsAccordionHeading"
	    >
	    <button
	      class="accordion-button collapsed p-2"
	      type="button"
	      data-bs-toggle="collapse"
	      data-bs-target="#collapseBasicSearchTips"
	      aria-controls="collapseBasicSearchTips"
	      >
	      Tips: Basic search
	    </button>
	  </h2>
	  <div
	    id="collapseBasicSearchTips"
	    class="accordion-collapse collapse"
	    aria-labelledby="basicSearchTipsAccordionHeading"
	    data-bs-parent="#searchTipsAccordion"
	    >
	    <div class="accordion-body">
	      <p>Basic search performs a case-insensitive containment search in the fields listed in the search form placeholder.</p>
	      <p>Things which Basic Search does <strong>not</strong> enable you to do:
		<ul>
		  <li>use boolean operators</li>
		  <li>multi-term search (<em>e.g.</em> with comma-separated query)</li>
		</ul>
	      </p>
	    </div>
	  </div>
	</div>
	<div class="accordion-item">
	  <h2
	    class="accordion-header"
	    id="advancedSearchTipsAccordionHeading"
	    >
	    <button
	      class="accordion-button collapsed p-2"
	      type="button"
	      data-bs-toggle="collapse"
	      data-bs-target="#collapseAdvancedSearchTips"
	      aria-controls="collapseAdvancedSearchTips"
	      >
	      Tips: Advanced search
	    </button>
	  </h2>
	  <div
	    id="collapseAdvancedSearchTips"
	    class="accordion-collapse collapse"
	    aria-labelledby="advancedSearchTipsAccordionHeading"
	    data-bs-parent="#searchTipsAccordion"
	    >
	    <div class="accordion-body">
	      <h3>Fundamentals</h3>
	      <p>Advanced search is based on (combinations of) search queries in the form</p>
	      <p class="text-center">[ field ] - [ lookup ] - [ value ]</p>
	      <p>in which <em>field</em> is one of the enabled search fields (typically one of the model's database fields), <em>lookup</em> is a lookup function (see details below), and <em>value</em> is the query string. Which field/lookup combinations are available depends on which model is being searched.</p>

	      <h3>Lookup functions</h3>
	      <p><em>N.B.: which lookup functions are available depends on which field is being queried.</em></p>
	      <table class="table">
		<tr><td><em>icontains</em></td><td>case-insensitive containment</td></tr>
		<tr><td><em>contains</em></td><td>case-sensitive containment</td></tr>
		<tr><td><em>istartswith</em></td><td>case-insensitive start match</td></tr>
		<tr><td><em>exact</em></td><td>exact match (full field value from beginning to end; case sensitive)</td></tr>
		<tr><td><em>year</em></td><td>YYYY format</td></tr>
		<tr><td><em>month</em></td><td>MM format</td></tr>
		<tr><td><em>gte</em></td><td>greater than or equal</td></tr>
		<tr><td><em>lte</em></td><td>less than or equal</td></tr>
		<tr><td><em>range</em></td><td>inclusive begin to end interval; format: begin,end</td></tr>
		<tr><td><em>iregex</em></td><td>case-insensitive <a href="https://en.wikipedia.org/wiki/Regular_expression" class="p-0" target="_blank" rel="nofollow">regular expression</a> pattern match</td></tr>
		<tr><td><em>regex</em></td><td>case-sensitive <a href="https://en.wikipedia.org/wiki/Regular_expression" class="p-0" target="_blank" rel="nofollow">regular expression</a> pattern match</td></tr>
	      </table>

	      <h3>Limitations</h3>
	      <p>Things which Advanced Search does <strong>not</strong> (yet) enable you to do:
		<ul>
		  <li>use the unary NOT on a query</li>
		  <li>have more than one query for a given field/lookup combination (tip: use regex matching instead)</li>
		  <li>full-text search of publications or submissions</li>
		  <li>combining queries with OR (tip/patch: use regex matching instead)</li>
		  <li>perform arbitrarily complex query combinations</li>
		</ul>
	      </p>

	      <h3>Examples</h3>
	      <table class="table table-striped">
		<thead>
		  <tr>
		    <th scope="col">Objects wanted</th>
		    <th scope="col">Field</th>
		    <th scope="col">Lookup</th>
		    <th scope="col">Value</th>
		  </tr>
		</thead>
		<tbody>
		  <tr>
		    <td>All with "quantum" followed by "chain" in abstract</td>
		    <td>Abstract</td>
		    <td><em>iregex</em></td>
		    <td>quantum[&nbsp;\w]+chain</td>
		  </tr>
		</tbody>
	      </table>
	    </div>
	  </div>
	</div>
      </div>
    </div>
  </div>
  <hr>
  <ul
    class="nav nav-pills nav-justified flex-column flex-sm-row mb-3 justify-content-center"
    role="tablist"
    >
    <li
      v-for="(availableTab, index) in availableTabs"
      class="flex-sm-fill text-sm-center nav-item"
      role="presentation"
      >
      <button
	class="nav-link mx-auto"
	:class="index == 0 ? 'active' : ''"
	:id="availableTab.label + '-tab'"
	data-bs-toggle="pill"
	:data-bs-target="'#' + availableTab.label"
	type="button"
	role="tab"
	aria-controls="availableTab.label"
	aria-selected="true"
	>
	{{ availableTab.label }}
      </button>
    </li>
  </ul>
  <hr>
  <div
    class="tab-content"
    id="tabContent">
    <div
      v-for="(availableTab, index) in availableTabs"
      class="tab-pane fade show"
      :class="index == 0 ? 'active' : ''"
      :id="availableTab.label"
      role="tabpanel"
      :aria-labelledby="availableTab.label + '-tab'"
      >
      <searchable-objects-table
	:object_type="availableTab.objectType"
	:url="availableTab.url"
	:initial_filter="initialQuery"
	>
      </searchable-objects-table>
    </div>
  </div>
</div>
</template>

<script>
const headers = new Headers();
headers.append('Accept', 'application/json; version=0')

import { ref, onMounted } from '@vue/composition-api'

import SearchableObjectsTable from './SearchableObjectsTable.vue'

export default {
    name: "search",
    components: {
	SearchableObjectsTable,
    },
    props: {
        initial_filter: {
            type: String,
            required: false
        },
    },
    setup(props, context) {
	const availableTabs = ref([])
	const initialQuery = ref('')

	const fetchAvailableTabs = async () => {
	    fetch('/api/available_search_tabs/', {headers: headers})
		.then(stream => stream.json())
		.then(data => {
		    availableTabs.value = data
		})
	    .catch(error => console.error(error))
	}

	onMounted( () => {
	    fetchAvailableTabs()
	    initialQuery.value = JSON.parse(document.getElementById('json_q').textContent)
	})
	// Close search form in header in case it is open
	onMounted(() => document.getElementById('header-search-close-btn').click())

	return {
	    availableTabs,
	    initialQuery
	}
    },
}
</script>
