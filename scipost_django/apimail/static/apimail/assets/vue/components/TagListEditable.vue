<template>
<div>
  <h3>Your current tags:</h3>
  <table class="table">
    <tr v-for="tag in tags" class="mb-4">
      <td>
	<button
	  class="btn btn-sm p-1"
	  :style="'background-color: ' + tag.bg_color"
	  >
	  <small :style="'color: ' + tag.text_color">{{ tag.label }}</small>
	</button>
      </td>
      <td>
	<button
	  class="float-right bg-danger text-white px-1 py-0"
	  @click.stop="deleteTag(tag.pk)"
	  >
	  <small>Delete</small>
	</button>
      </td>
    </tr>
  </table>
  <h3>Create a new tag:</h3>
  <template v-if="!responseOK">
    <div class="bg-danger text-white">
      <p class="mx-2 mb-0 p-2">
	The server responded with errors, please check and try again.
      </p>
      <ul class="pb-2">
	<li class="m-2" v-for="(field, error) in response_body_json">
	  {{ error }}:&emsp;{{ field }}
	</li>
      </ul>
    </div>
  </template>
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
	placeholder="Up to 16 characters"
	>
      </b-form-input>
    </b-form-group>
    <b-form-group
      id="text-color"
      label="Text color:"
      label-for="input-text-color"
      >
      <b-form-input
	id="input-text-color"
	v-model="newTagForm.textColor"
	type="color">
      </b-form-input>
    </b-form-group>
    <b-form-group
      id="bg-color"
      label="Background color:"
      label-for="input-bg-color"
      >
      <b-form-input
	id="input-bg-color"
	v-model="newTagForm.bgColor"
	type="color">
      </b-form-input>
    </b-form-group>
  </b-form>
  <button
    class="btn btn-success text-white"
    @click.stop.prevent="createNewTag"
    >
    Create new Tag
  </button>
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
		textColor: null,
		bgColor: null,
	    },
	    responseOK: true,
	    response_body_json: null,
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
			  'text_color': this.newTagForm.textColor,
			  'bg_color': this.newTagForm.bgColor,
		      })
		  })
		.then(response => {
		    if (response.ok) {
			this.responseOK = true
			this.newTagForm.label = null
			this.newTagForm.textColor = null
			this.newTagForm.bgColor = null
			this.$emit('fetchtags')
		    }
		    else {
			this.responseOK = false
		    }
		    return response.json()
		})
		.then(responsejson => {
		    this.response_body_json = responsejson
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
