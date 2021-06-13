<template>
<div>
  <div
    class="nav nav-pills nav-justified me-3 mb-3 justify-content-center"
    role="tablist"
    >
    <button
      class="nav-link active"
      data-bs-toggle="pill"
      :data-bs-target="'#basicSearchTab-' + object_type"
      type="button" role="tab"
      @click="advancedSearchIsOn = false"
      aria-controls="basic-search"
      aria-selected="true"
      >
      Basic Search
    </button>
    <button
      class="nav-link"
      data-bs-toggle="pill"
      :data-bs-target="'#advancedSearchTab-' + object_type"
      type="button"
      role="tab"
      @click="advancedSearchIsOn = true"
      aria-controls="advanced-search"
      aria-selected="true"
      >
      Advanced Search
    </button>
  </div>
  <div
    class="tab-content p-2 flex-fill"
    :id="'tabContent-' + object_type"
    >
    <div
      class="tab-pane fade show active"
      :id="'basicSearchTab-' + object_type"
      role="tabpanel"
      aria-labelledby="basic-search-tab"
      >
      <div class="row">
	<div class="col-sm-10 col-md-11">
	  <div class="form-floating">
	    <input
	      v-model="basicSearchQuery"
	      type="text"
	      class="form-control"
	      id="basicSearchInput"
	      :placeholder="basicSearchInputLabel"
	      >
	    <label for="basicSearchInput">
	      {{ basicSearchInputLabel }}
	    </label>
	  </div>
	</div>
	<div class="col-sm-2 col-md-1 align-self-center">
	  <button
	    v-if="basicSearchQuery"
	    class="btn btn-sm btn-outline-secondary"
	    type="button"
	    data-bs-toggle="tooltip"
	    title="Clear value"
	    @click="basicSearchQuery = ''"
	    >
	    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
	    </svg>
	  </button>
	</div>
      </div>
    </div>
    <div
      class="tab-pane fade"
      :id="'advancedSearchTab-' + object_type"
      role="tabpanel"
      aria-labelledby="advanced-search-tab"
      >
      <div class="row">
	<div class="col-sm-6 col-md-3 g-0">
	  <div class="form-floating">
	    <select
	      class="form-select input-group-text"
	      id="selectNewQueryField"
	      v-model="newQueryField"
	      >
	      <option
		v-for="filteringField in filteringFieldsAdvanced"
		:value="filteringField.field"
		>
		<strong>{{ filteringField.label }}</strong>
	      </option>
	    </select>
	    <label for="selectNewQueryField">
	      Search field
	    </label>
	  </div>
	</div>
	<div class="col-sm-6 col-md-3 g-0">
	  <div class="form-floating">
	    <select
	      class="form-select input-group-text"
	      id="selectNewQueryLookup"
	      v-model="newQueryLookup"
	      >
	      <option
		v-for="(lookup, index) in allowedLookups"
		:value="lookup"
		>
		<em>{{ lookup }}</em>
	      </option>
	    </select>
	    <label for="selectNewQueryLookup">
	      Lookup function
	    </label>
	  </div>
	</div>
	<div class="col-sm-10 col-md-5 g-0">
	  <div class="form-floating">
	    <input
	      v-model="newQueryValue"
	      type="text"
	      class="form-control"
	      id="inputNewQueryValue"
	      >
	    <label for="inputNewQueryValue">
	      Value
	    </label>
	  </div>
	</div>
	<div class="col-sm-2 col-md-1 align-self-center">
	  <button
	    v-if="newQueryValue"
	    class="btn btn-sm btn-outline-secondary"
	    type="button"
	    data-bs-toggle="tooltip"
	    title="Clear value"
	    @click="newQueryValue = ''"
	    >
	    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
	    </svg>
	  </button>
	  <button
	    v-if="newQueryIsValid"
	    class="btn btn-sm btn-outline-success"
	    type="button"
	    data-bs-toggle="tooltip"
	    title="Add query to list"
	    @click="addNewQueryToList"
	    >
	    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
	    </svg>
	  </button>
	</div>
      </div>
      <div
	v-if="queriesList.length > 0"
	class="row"
	>
	<div class="col">
	  <h3 class="mb-2">Applied&nbsp;queries <small class="text-muted">(combined with <em>AND</em>)</small>:</h3>
	  <table class="table">
	    <thead>
	      <th scope="col">Field</th>
	      <th scope="col">Lookup</th>
	      <th scope="col">Value</th>
	      <th scope="col">Actions</th>
	    </thead>
	    <tbody>
	      <tr
		v-for="query in queriesList"
		:class="query.active ? '' : 'text-muted text-decoration-line-through'"
		>
		<td>{{ query.field }}</td>
		<td>{{ query.lookup }}</td>
		<td>{{ query.value }}</td>
		<td>
		  <div
		    class="btn-group"
		    role="group"
		    aria-label="query action buttons"
		    >
		    <button
		      class="btn btn-sm btn-outline-warning"
		      type="button"
		      data-bs-toggle="tooltip"
		      title="Toggle on/off"
		      @click="query.active = !query.active"
		      >
		      <span v-if="query.active">
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-toggle-on" viewBox="0 0 16 16"><path d="M5 3a5 5 0 0 0 0 10h6a5 5 0 0 0 0-10H5zm6 9a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>
			</svg>
		      </span>
		      <span v-else>
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-toggle-off" viewBox="0 0 16 16"><path d="M11 4a4 4 0 0 1 0 8H8a4.992 4.992 0 0 0 2-4 4.992 4.992 0 0 0-2-4h3zm-6 8a4 4 0 1 1 0-8 4 4 0 0 1 0 8zM0 8a5 5 0 0 0 5 5h6a5 5 0 0 0 0-10H5a5 5 0 0 0-5 5z"/>
			</svg>
		      </span>
		    </button>
		    <button
		      class="btn btn-sm btn-outline-danger"
		      type="button"
		      data-bs-toggle="tooltip"
		      title="Discard"
		      @click="discardQuery(query)"
		      >
		      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-trash-fill" viewBox="0 0 16 16"><path d="M2.5 1a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1H3v9a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V4h.5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H10a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1H2.5zm3 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5zM8 5a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7A.5.5 0 0 1 8 5zm3 .5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 1 0z"/>
		      </svg>
		    </button>
		  </div>
		</td>
	      </tr>
	    </tbody>
	  </table>
	</div>
      </div>
    </div>
  </div>

  <div class="row mb-4">
    <div class="col-md-2 align-self-center d-flex justify-content-center">
      <span class="badge bg-primary mb-2">
	{{ totalRows }} result<span v-if="totalRows != 1">s</span>
      </span>
    </div>
    <div class="col-md-6">
      <nav aria-label="navigation">
	<ul class="mb-2 pagination justify-content-center align-self-center">
	  <li
	    v-for="pagenr in paginatorButtonData"
	    class="page-item"
	    >
	    <span v-if="pagenr > 0">
	      <a
		class="page-link"
		:class="{ 'bg-primary text-white': pagenr === currentPage }"
		@click="currentPage = pagenr"
		>
		{{ pagenr }}
	      </a>
	    </span>
	    <span v-else>
	      <a class="page-link" disabled>&hellip;</a>
	    </span>
	  </li>
	</ul>
      </nav>
    </div>
    <div class="col-md-4 d-flex justify-content-center">
      <div class="mb-2 align-self-center">Per&nbsp;page:</div>
      <div class="mb-2 form-check form-check-inline align-self-center">
	<div class="btn-group" role="group">
	  <div v-for="option in perPageOptions">
	    <input
	      v-model="perPage"
	      class="btn-check"
	      type="radio"
	      name="btnRadioperPage"
	      :id="'btnRadioperPage-' + option"
	      :value="option"
	      >
	    <label
	      class="btn btn-sm"
	      :class="perPage === option ? 'btn-primary text-white' : 'btn-outline-primary'"
	      :for="'btnRadioperPage-' + option"
	      >
	      {{ option }}
	    </label>
	  </div>
	</div>
      </div>
    </div>
  </div>

  <div class="row">
    <div class="col">
      <div
	v-if="errorFetchingObjects"
	class="text-danger"
	>
	{{ errorFetchingObjects }}
      </div>
      <div
	v-if="fetchingObjects"
	class="text-center"
	>
	<button
	  class="btn btn-outline-primary"
	  type="button" disabled
	  >
	  <span
	    class="spinner-grow spinner-grow-sm"
	    role="status"
	    aria-hidden="true"
	    >
	  </span>
	  Loading...
	</button>
      </div>
      <div v-else>
	<table class="table table-bordered">
	  <tbody>
	    <tr v-for="object in objects">
	      <object-row-details
		:object_type="object_type"
		:object="object"
		>
	      </object-row-details>
	    </tr>
	  </tbody>
	</table>
      </div>
    </div>
  </div>
</div>
</template>

<script>
const headers = new Headers();
headers.append('Accept', 'application/json; version=0')

import { ref, computed, watch, onMounted } from '@vue/composition-api'

import ObjectRowDetails from './ObjectRowDetails/ObjectRowDetails.vue'

var debounce = require('lodash.debounce')

const XRegExp = require('xregexp')

export default {
    name: 'searchable-objects-table',
    components: {
	ObjectRowDetails,
    },
    props: {
	object_type: {
	    type: String,
	    required: true
	},
        displayfields: {
            type: Array,
            required: true
        },
        paginated: true,
        numbered: false,
        url: {
            type: String,
            required: true
        },
        initial_filter: {
            type: String,
            required: false
        },
    },
    setup(props) {
	const advancedSearchIsOn = ref(false)
	const basicSearchQuery = ref('')
	const newQueryField = ref(null)
	const allowedLookups = ref([])
	const newQueryLookup = ref('')
	const newQueryValue = ref('')
	const queriesList = ref([])
	const totalRows = ref(0)
	const perPageOptions = ref([8, 16, 32, 64])
	const perPage = ref(16)
	const currentPage = ref(1)
	const objects = ref([])
	const fetchingObjects = ref(false)
	const errorFetchingObjects = ref(null)
	const filteringFieldsBasic = ref([])
	const filteringFieldsAdvanced = ref([])

	const fetchFilteringFields = async () => {
            fetch(`/api/${props.url}/filtering_options`, {headers: headers})
                .then(stream => stream.json())
                .then(data => {
		    filteringFieldsBasic.value = data.basic
		    filteringFieldsAdvanced.value = data.advanced.map(
			function(option) {
			    return {
				label: option.label,
				field: option.field,
				lookups: option.lookups
			    }
			})
		})
		.catch(error => console.error(error))
	}

        const basicSearchInputLabel = computed(() => {
            var label = 'Search in: '
            var counter = 0
            filteringFieldsBasic.value.forEach(
                (filteringField) => {
                    if (counter > 0) {
                        label += ', '
                    }
                    counter += 1
                    label += filteringField
                }
            )
            return label
	})

	const getAllowedLookups = () => {
	    if (newQueryField.value) {
		allowedLookups.value = filteringFieldsAdvanced.value.find(
		    el => el.field == newQueryField.value
		).lookups.filter( // remove already-used lookups
		    item => !queriesList.value.some( el => {
			return (el.field === newQueryField.value &&
				el.lookup === item)
			})
		)
		// Set choice to first value by default
		newQueryLookup.value = allowedLookups.value[0]
	    }
	    else allowedLookups.value = []
	}

	const newQueryIsValid = computed(() => {
	    if (newQueryField.value && newQueryLookup.value && newQueryValue.value  // newQuery exists
		// and newQuery's field/lookup combination is not already in queriesList:
		&& !queriesList.value.some( el => {
		    return (el.field === newQueryField.value &&
			    el.lookup === newQueryLookup.value)
		})
	       ) { // Validation checks per lookup type
		if (newQueryLookup.value.includes('regex')) {
		    try { // check if the regex is a valid regular expression
			const test = RegExp(newQueryValue.value)
		    } catch (error) {
			return false
		    }
		}
		return true  // All checks passed
	    }
	    return false
	})

	const addNewQueryToList = () => {
	    queriesList.value.push({
		field: newQueryField.value,
		lookup: newQueryLookup.value,
		value: newQueryValue.value,
		active: true
	    })
	    newQueryField.value = null
	    newQueryLookup.value = ''
	    newQueryValue.value = ''
	}

	const discardQuery = (query) => {
	    queriesList.value = queriesList.value.filter((item) => item !== query)
	}

	const queryParameters = computed(() => {
	    var parameters = `?limit=${perPage.value}&offset=${perPage.value * (currentPage.value - 1)}`
	    if (!advancedSearchIsOn.value) { // basic search
		if (basicSearchQuery.value) parameters += '&search=' + basicSearchQuery.value
	    }
	    else {
		if (newQueryIsValid.value) {
		    parameters += `&${newQueryField.value}__${newQueryLookup.value}=`
		    if (newQueryLookup.value.includes('regex')) { // careful with regex (also below)
			parameters += encodeURIComponent(`${newQueryValue.value}`).replace('%20', '+')
		    }
		    else parameters += `${newQueryValue.value}`
		}
		queriesList.value.forEach( (query) => {
		    if (query.active) {
			parameters += `&${query.field}__${query.lookup}=`
			if (query.lookup.includes('regex')) { // careful with regex (also above)
			    parameters += encodeURIComponent(`${query.value}`).replace('%20', '+')
			}
			else parameters += `${query.value}`
		    }
		})
	    }
            if (props.initial_filter) {
                parameters += ('&' + props.initial_filter)
            }
	    return parameters
	})

	const getObjects = debounce(
	    async () => {
		fetchingObjects.value = true
		errorFetchingObjects.value = null
		try {
		    const response = await fetch(`/api/${props.url}${queryParameters.value}`, {headers: headers})
		    const json = await response.json()
		    objects.value = json.results
		    totalRows.value = json.count
		} catch (errors) {
		    errorFetchingObjects.value = errors
		} finally {
		    fetchingObjects.value = false
		}
	    },
	    300)

	const paginatorButtonData = computed(() => {
	    var maxPageNr = Math.max(1, Math.ceil(totalRows.value/perPage.value))
	    let buttonData = [1,]
	    if (currentPage.value > 4) buttonData.push(0)
	    if (currentPage.value > 3) buttonData.push(currentPage.value - 2)
	    if (currentPage.value > 2) buttonData.push(currentPage.value - 1)
	    if (currentPage.value > 1) buttonData.push(currentPage.value)
	    if (currentPage.value < maxPageNr - 1) buttonData.push(currentPage.value + 1)
	    if (currentPage.value < maxPageNr - 2) buttonData.push(currentPage.value + 2)
	    if (currentPage.value < maxPageNr - 3) buttonData.push(0)
	    if (currentPage.value < maxPageNr) buttonData.push(maxPageNr)
	    return buttonData
	})

	onMounted(getObjects)
	onMounted(fetchFilteringFields)

	watch(basicSearchQuery, getObjects)
	watch(perPage, () => currentPage.value = 1)
	watch(newQueryField, getAllowedLookups)
	watch(queriesList, () => { if (newQueryField.value) getAllowedLookups()}) // to cover binning a query
	watch(queryParameters, getObjects)

	return {
	    advancedSearchIsOn,
	    basicSearchInputLabel,
	    basicSearchQuery,
	    newQueryField,
	    allowedLookups,
	    newQueryLookup,
	    newQueryValue,
	    newQueryIsValid,
	    addNewQueryToList,
	    discardQuery,
	    queriesList,
	    totalRows,
	    perPageOptions,
	    perPage,
	    paginatorButtonData,
	    currentPage,
	    objects,
	    fetchingObjects,
	    errorFetchingObjects,
	    filteringFieldsBasic,
	    filteringFieldsAdvanced
	}
    }
}
</script>
