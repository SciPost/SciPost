<template>
<div>
  <h3>Your current tags:</h3>
  <table class="table">
    <tr v-for="tag in tags" class="mb-4">
      <td>
	<b-button
	  size="sm"
	  class="p-1"
	  :variant="tag.variant"
	  >
	  {{ tag.unicode_symbol }}
	</b-button>
      </td>
      <td>{{ tag.label }}</td>
      <td>
	<b-button class="float-right bg-danger text-white px-1 py-0" @click.stop="deleteTag(tag.pk)">
	  <small>Delete</small>
	</b-button>
      </td>
    </tr>
  </table>
  <h3>Create a new tag:</h3>
  <b-form
    >
    <b-form-group
      id="label"
      label="Label:"
      label-for="input-label"
      >
      <b-form-input
	id="input-label"
	v-model="newTagForm.label"
	required
	placeholder="Enter a label for your new Tag"
	>
      </b-form-input>
    </b-form-group>
    <b-form-group
      id="unicode_symbol"
      label="Unicode symbol:"
      label-for="input-unicode-symbol"
      >
      <b-form-input
	id="input-unicode-symbol"
	v-model="newTagForm.unicode_symbol"
	required
	placeholder="Enter a single (arbitrary) unicode character"
	>
      </b-form-input>
    </b-form-group>
    <b-form-group
      id="variant"
      label-for="input-variant"
      >
      <label>Variant
	<span v-if="newTagForm.variant"> selected: <b-button class="my-2 px-1 py-0" :variant="newTagForm.variant">{{ newTagForm.variant }}</b-button></span>
	<span v-else>:</span>
      </label>
      <b-form-radio-group
      	id="input-variant"
      	v-model="newTagForm.variant"
	buttons
	>
	<b-form-radio v-for="variant in variantOptions" class="px-1 py-0" :value="variant" :button-variant="variant">{{ variant }}</b-form-radio>
      </b-form-radio-group>

    </b-form-group>

  </b-form>
  <b-button
    variant="success"
    class="text-white"
    @click.stop.prevent="createNewTag"
    >
    Create new Tag
  </b-button>
</div>
</template>

<script>
import Cookies from 'js-cookie'

var csrftoken = Cookies.get('csrftoken');

export default {
    props: {
	tags: {
	    type: Array,
	    required: false,
	},
    },
    data() {
	return {
	    newTagForm: {
		label: null,
		unicode_symbol: null,
		variant: null
	    },
	    variantOptions: [
		'primary', 'secondary', 'success', 'warning', 'danger', 'info', 'dark',
	    ]
	}
    },
    methods: {
	createNewTag () {
	    fetch('/mail/api/user_tag/create',
		  {
		      method: 'POST',
		      headers: {
			  "X-CSRFToken": csrftoken,
	    		  "Content-Type": "application/json; charset=utf-8"
		      },
		      body: JSON.stringify({
			  'label': this.newTagForm.label,
			  'unicode_symbol': this.newTagForm.unicode_symbol,
			  'variant': this.newTagForm.variant,
		      })
		  })
		.then(response => {
		    if (response.ok) {
			this.newTagForm.label = null,
			this.newTagForm.unicode_symbol = null,
			this.newTagForm.variant = null
			this.$emit('fetchtags')
		    }
		    else {
			console.log(response.data)
		    }
		})
		.catch(error => console.error(error))
	},
	deleteTag (pk) {
	    if (confirm("Do you really want to delete this tag? " +
			"It will be immediately removed from all messages.")) {
		fetch('/mail/api/user_tag/' + pk + '/delete',
		      {
			  method: 'DELETE',
			  headers: {
			      "X-CSRFToken": csrftoken,
			  }
		      })
		    .then(response => {
			if (response.ok) {
			    this.$emit('fetchtags')
			}
		    })
		    .catch(error => console.error(error))
	    }
	}
    }
}
</script>
