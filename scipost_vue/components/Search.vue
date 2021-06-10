<template>
<div>
  <h1>Search</h1>

  <ul class="nav nav-pills mb-3" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" id="publications-tab" data-bs-toggle="pill" data-bs-target="#publications" type="button" role="tab" aria-controls="publications" aria-selected="true">Publications</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="submissions-tab" data-bs-toggle="pill" data-bs-target="#submissions" type="button" role="tab" aria-controls="submissions" aria-selected="true">Submissions</button>
    </li>
  </ul>
  <div class="tab-content" id="tabContent">
    <div class="tab-pane fade show active" id="publications" role="tabpanel" aria-labelledby="publications-tab">
      <searchable-objects-table
	:object_type="'publication'"
	:displayfields="[{ field: 'doi_label', label: 'DOI label' }, { field: 'url', label: 'URL' }]"
	:url="'publications'"
	>
      </searchable-objects-table>
    </div>
    <div class="tab-pane fade" id="submissions" role="tabpanel" aria-labelledby="submissions-tab">
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
