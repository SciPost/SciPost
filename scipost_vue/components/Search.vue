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
	      class="accordion-button p-2"
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
	      class="accordion-button p-2"
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
      class="flex-sm-fill text-sm-center nav-item"
      role="presentation"
      >
      <button
	class="nav-link mx-auto active"
	id="publications-tab"
	data-bs-toggle="pill"
	data-bs-target="#publications"
	type="button"
	role="tab"
	aria-controls="publications"
	aria-selected="true"
	>
	Publications
      </button>
    </li>
    <li
      class="flex-sm-fill text-sm-center nav-item"
      role="presentation"
      >
      <button
	class="nav-link mx-auto"
	id="submissions-tab"
	data-bs-toggle="pill"
	data-bs-target="#submissions"
	type="button"
	role="tab"
	aria-controls="submissions"
	aria-selected="true"
	>
	Submissions
      </button>
    </li>
  </ul>
  <hr>
  <div
    class="tab-content"
    id="tabContent">
    <div
      class="tab-pane fade show active"
      id="publications"
      role="tabpanel"
      aria-labelledby="publications-tab"
      >
      <searchable-objects-table
	:object_type="'publication'"
	:displayfields="[{ field: 'doi_label', label: 'DOI label' }, { field: 'url', label: 'URL' }]"
	:url="'publications'"
	>
      </searchable-objects-table>
    </div>
    <div
      class="tab-pane fade"
      id="submissions"
      role="tabpanel"
      aria-labelledby="submissions-tab"
      >
      <searchable-objects-table
	:object_type="'submission'"
	:displayfields="[{ field: 'title', label: 'Title'}, { field: 'identifier', label: 'Identifier' }]"
	:url="'submissions'"
	>
      </searchable-objects-table>
    </div>
  </div>
</div>
</template>

<script>
import SearchableObjectsTable from './SearchableObjectsTable.vue'

export default {
    name: "search",
    components: {
	SearchableObjectsTable,
    },
    setup() {
    },
}
</script>
