<template>
<div>
  <div class="d-flex align-items-start">
    <div class="nav flex-column nav-pills me-3" role="tablist" aria-orientation="vertical">
      <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#basic-search" type="button" role="tab" @click="advancedSearchIsOn = false" aria-controls="basic-search" aria-selected="true">Basic Search</button>
      <button class="nav-link" data-bs-toggle="pill" data-bs-target="#advanced-search" type="button" role="tab" @click="advancedSearchIsOn = true" aria-controls="advanced-search" aria-selected="true">Advanced Search</button>
    </div>
    <div class="tab-content" id="tabContent">
      <div class="tab-pane fade show active" id="basic-search" role="tabpanel" aria-labelledby="basic-search-tab">
	<div class="input-group mb-3">
	  <input v-model="basicSearchQuery" type="text" class="form-control" :placeholder="basicSearchPlaceholder">
	  <button class="btn btn-secondary" type="button" @click="basicSearchQuery = ''">Clear</button>
	</div>
      </div>
      <div class="tab-pane fade" id="advanced-search" role="tabpanel" aria-labelledby="advanced-search-tab">
	<div class="input-group mb-3">
	  <select
	    class="form-select input-group-text"
	    v-model="newClauseField"
	    placeholder="Choose a field"
	    >
	    <option v-for="filteringField in filteringFieldsAdvanced" :value="filteringField.field">
	      <strong>{{ filteringField.label }}</strong>
	    </option>
	  </select>
	  <select class="form-select input-group-text" v-model="newClauseLookup">
	    <option v-for="lookup in allowedLookups" value="lookup">
	      <em>{{ lookup }}</em>
	    </option>
	  </select>
	  <input type="text" class="form-control" v-model="newClauseValue">
	  <button class="btn btn-secondary" type="button" @click="newClauseValue = ''">Clear</button>
	</div>
	<div class="input-group mb-3" v-for="filteringField in filteringFieldsAdvanced">
	  <span class="input-group-text"><strong>{{ filteringField.label }}</strong></span>
	  <span class="input-group-text"><strong>{{ filteringField.lookup }}</strong></span>
	  <input type="text" class="form-control" v-model="filteringField.filter">
	  <button class="btn btn-secondary" type="button" @click="filteringField.filter = ''">Clear</button>
	</div>
      </div>
    </div>
  </div>

  <div class="row">
    <div v-if="errorFetchingObjects">
      {{ errorFetchingObjects }}
      {{ url }}
    </div>

    <table class="table">
      <thead>
	<tr>
	  <th v-for="field in displayfields">{{ field.label }}</th>
	</tr>
      </thead>
      <tbody>
	<tr v-for="object in objects">
	  <td v-for="field in displayfields">{{ object[field.field] }}</td>
	</tr>
      </tbody>
    </table>
  </div>
  </div>
</template>

<script>
const headers = new Headers();
headers.append('Accept', 'application/json; version=0')

import { ref, computed, watch, onMounted } from '@vue/composition-api'

var debounce = require('lodash.debounce')

export default {
    name: 'searchable-objects-table',
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

        const basicSearchPlaceholder = computed(() => {
            var placeholder = 'Search in: '
            var counter = 0
            filteringFieldsBasic.value.forEach(
                (filteringField) => {
                    if (counter > 0) {
                        placeholder += ', '
                    }
                    counter += 1
                    placeholder += filteringField
                }
            )
            return placeholder
	})

	const getAllowedLookups = () => {
	    allowedLookups.value = filteringFieldsAdvanced.value.find(
		el => el.field == newClauseField.value).lookups
	}

	const queryParameters = computed(() => {
	    var parameters = '?limit=20&offset=0'
	    if (!advancedSearchIsOn.value) { // basic search
		parameters += '&search=' + basicSearchQuery.value
	    }
            else {
                filteringFieldsAdvanced.value.forEach((filteringField) => {
                    if (filteringField.filter) {
                        parameters += ('&' + filteringField.field + '__'
                                       + filteringField.lookup + '=' + filteringField.filter)
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
		try {
		    const response = await fetch(`/api/${props.url}/${queryParameters.value}`)
		    const json = await response.json()
		    objects.value = json.results
		} catch (errors) {
		    errorFetchingObjects.value = errors
		} finally {
		    fetchingObjects.value = false
		}
	    },
	    300)

	onMounted(getObjects)
	onMounted(fetchFilteringFields)

	watch(basicSearchQuery, getObjects)
	watch(newClauseField, getAllowedLookups)
	watch(filteringFieldsAdvanced, getObjects)

	return {
	    advancedSearchIsOn,
	    basicSearchPlaceholder,
	    basicSearchQuery,
	    newClauseField,
	    allowedLookups,
	    newClauseLookup,
	    newClauseValue,
	    objects,
	    fetchingObjects,
	    errorFetchingObjects,
	    filteringFieldsBasic,
	    filteringFieldsAdvanced
	}
    }
}
</script>
