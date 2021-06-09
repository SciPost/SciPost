<template>
<div>
  {{ searchTabIndex }}
  <div class="d-flex align-items-start">
    <div class="nav flex-column nav-pills me-3" role="tablist" v-model="searchTabIndex" aria-orientation="vertical">
      <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#basic-search" type="button" role="tab" aria-controls="basic-search" aria-selected="true">Basic Search</button>
      <button class="nav-link" data-bs-toggle="pill" data-bs-target="#advanced-search" type="button" role="tab" aria-controls="advanced-search" aria-selected="true">Advanced Search</button>
    </div>
    <div class="tab-content" id="tabContent">
      <div class="tab-pane fade show active" id="basic-search" role="tabpanel" aria-labelledby="basic-search-tab">
	<div class="input-group mb-3">
	  <input v-model="basicSearchQuery" type="text" class="form-control">
	  <button class="btn btn-secondary" type="button" @click="basicSearchQuery = ''">Clear</button>
	</div>
      </div>
      <div class="tab-pane fade" id="advanced-search" role="tabpanel" aria-labelledby="advanced-search-tab">
	Advanced search
      </div>
    </div>
  </div>

  <div class="row">
    <div v-if="error">
      {{ error }}
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
	  <td v-for="field in displayfields">{{ object[field.key] }}</td>
	</tr>
      </tbody>
    </table>
  </div>
  </div>
</template>

<script>
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
	excluded_filter_fields: {
	    type: Array,
	    required: false
	},
    },
    setup(props) {
	const searchTabIndex = ref(0)
	const basicSearchQuery = ref('')
	const objects = ref([])
	const fetching = ref(false)
	const error = ref(null)

	const queryParameters = computed(() => {
	    var parameters = '?limit=20&offset=0'
	    if (searchTabIndex.value == 0) { // basic search
		parameters += '&search=' + basicSearchQuery.value
	    }
            // else {
            //     filteringFieldsAdvanced.forEach((filteringField) => {
            //         if (filteringField.filter) {
            //             parameters += ('&' + filteringField.key + '__'
            //                            + filteringField.lookup + '=' + filteringField.filter)
            //         }
            //     })
            // }
            if (props.initial_filter) {
                parameters += ('&' + props.initial_filter)
            }
	    return parameters
	})
	const getObjects = debounce(
	    async () => {
		fetching.value = true
		try {
		    const response = await fetch(`/api/${props.url}/${queryParameters.value}`)
		    const json = await response.json()
		    objects.value = json.results
		} catch (errors) {
		    error.value = errors
		} finally {
		    fetching.value = false
		}
	    },
	    300)

	onMounted(getObjects)

	watch(basicSearchQuery, getObjects)

	return {
	    searchTabIndex,
	    basicSearchQuery,
	    objects,
	    fetching,
	    error,
	}
    }
}
</script>
