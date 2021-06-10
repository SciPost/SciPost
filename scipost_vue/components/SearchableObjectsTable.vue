<template>
<div>
  <div class="d-flex align-items-start">
    <div class="nav flex-column nav-pills me-3" role="tablist" aria-orientation="vertical">
      <button class="nav-link active" data-bs-toggle="pill" :data-bs-target="'#basicSearchTab-' + object_type"
	      type="button" role="tab" @click="advancedSearchIsOn = false"
	      aria-controls="basic-search" aria-selected="true"
	      >Basic Search</button>
      <button class="nav-link" data-bs-toggle="pill" :data-bs-target="'#advancedSearchTab-' + object_type"
	      type="button" role="tab" @click="advancedSearchIsOn = true"
	      aria-controls="advanced-search" aria-selected="true"
	      >Advanced Search</button>
    </div>
    <div class="tab-content p-2 flex-fill" :id="'tabContent-' + object_type">
      <div class="tab-pane fade show active" :id="'basicSearchTab-' + object_type" role="tabpanel" aria-labelledby="basic-search-tab">
	<div class="row">
	  <div class="col-9">
	    <div class="form-floating">
	      <input v-model="basicSearchQuery" type="text" class="form-control" id="basicSearchInput" :placeholder="basicSearchInputLabel">
	      <label for="basicSearchInput">{{ basicSearchInputLabel }}</label>
	    </div>
	  </div>
	  <div class="col-3 align-self-center">
	    <button class="btn btn-secondary" type="button" @click="basicSearchQuery = ''">Clear</button>
	  </div>
	</div>
      </div>
      <div class="tab-pane fade" :id="'advancedSearchTab-' + object_type" role="tabpanel" aria-labelledby="advanced-search-tab">
	<div class="row">
	  <div class="col-3 g-0">
	    <div class="form-floating">
	      <select class="form-select input-group-text"
		      id="selectNewClauseField"
		      v-model="newClauseField"
		      >
		<option v-for="filteringField in filteringFieldsAdvanced" :value="filteringField.field">
		  <strong>{{ filteringField.label }}</strong>
		</option>
	      </select>
	      <label for="selectNewClauseField">Search field</label>
	    </div>
	  </div>
	  <div class="col-3 g-0">
	    <div class="form-floating">
	      <select class="form-select input-group-text"
		      id="selectNewClauseLookup"
		      v-model="newClauseLookup">
		<option v-for="(lookup, index) in allowedLookups" :value="lookup">
		  <em>{{ lookup }}</em>
		</option>
	      </select>
	      <label for="selectNewClauseLookup">Lookup function</label>
	    </div>
	  </div>
	  <div class="col-5 g-0">
	    <div class="form-floating">
	      <input type="text" class="form-control" id="inputNewClauseValue" v-model="newClauseValue">
	      <label for="inputNewClauseValue">Value</label>
	    </div>
	  </div>
	  <div class="col-1 align-self-center">
	    <button class="btn btn-secondary" type="button" @click="newClauseValue = ''">Clear</button>
	  </div>
	</div>
      </div>
    </div>
  </div>

  <div class="row">
    <div class="col">
      <div v-if="errorFetchingObjects">
	{{ errorFetchingObjects }}
	{{ url }}
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col">
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

  <div class="row">
    <div class="col-8">
      <nav aria-label="navigation">
	<ul class="pagination justify-content-center">
	  <li v-for="pagenr in paginatorButtonData" class="page-item">
	    <span v-if="pagenr > 0">
	      <a class="page-link" :class="{ 'bg-primary text-white': pagenr === currentPage }" @click="currentPage = pagenr">{{ pagenr }}</a>
	    </span>
	    <span v-else>
	      <a class="page-link" disabled>&hellip;</a>
	    </span>
	  </li>
	</ul>
      </nav>
    </div>
    <div class="col-4">
      Per&nbsp;page:
      <div class="form-check form-check-inline">
	<div class="btn-group" role="group">
	  <div v-for="option in perPageOptions">
	    <input v-model="perPage" class="btn-check" type="radio" name="btnRadioperPage" :id="'btnRadioperPage-' + option" :value="option">
	    <label class="btn btn-sm" :class="perPage === option ? 'btn-primary text-white' : 'btn-outline-primary'" :for="'btnRadioperPage-' + option">{{ option }}</label>
	  </div>
	</div>
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
	const newClauseField = ref(null)
	const allowedLookups = ref([])
	const newClauseLookup = ref('')
	const newClauseValue = ref('')
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
	    allowedLookups.value = filteringFieldsAdvanced.value.find(
		el => el.field == newClauseField.value).lookups
	    // Set choice to first value by default
	    newClauseLookup.value = allowedLookups.value[0]
	}

	const queryParameters = computed(() => {
	    var parameters = `?limit=${perPage.value}&offset=${perPage.value * (currentPage.value - 1)}`
	    if (!advancedSearchIsOn.value) { // basic search
		if (basicSearchQuery.value) parameters += '&search=' + basicSearchQuery.value
	    }
	    else {
		parameters += `&${newClauseField.value}__${newClauseLookup.value}=${newClauseValue.value}`
	    }
            if (props.initial_filter) {
                parameters += ('&' + props.initial_filter)
            }
	    return parameters
	})

	const getObjects = debounce(
	    async () => {
		fetchingObjects.value = true
		try {
		    const response = await fetch(`/api/${props.url}/${queryParameters.value}`)
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
	    if (currentPage.value < maxPageNr - 2) buttonData.push(currentPage.value + 1)
	    if (currentPage.value < maxPageNr - 3) buttonData.push(currentPage.value + 2)
	    if (currentPage.value < maxPageNr - 4) buttonData.push(0)
	    if (currentPage.value < maxPageNr) buttonData.push(maxPageNr)
	    return buttonData
	})

	onMounted(getObjects)
	onMounted(fetchFilteringFields)

	watch(basicSearchQuery, getObjects)
	watch(newClauseField, getAllowedLookups)
	watch(queryParameters, getObjects)

	return {
	    advancedSearchIsOn,
	    basicSearchInputLabel,
	    basicSearchQuery,
	    newClauseField,
	    allowedLookups,
	    newClauseLookup,
	    newClauseValue,
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
