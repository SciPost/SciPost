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
  <form>
    <div class="input-group mb-3">
      <span class="input-group-text">Label</span>
      <input
	type="text"
	class="form-control"
	v-model="newTagForm.label"
	placeholder="Up to 16 characters"
	>
    </div>
    <div class="input-group mb-3">
      <span class="input-group-text">Text color</span>
      <input
	type="color"
	class="form-control"
	v-model="newTagForm.textColor"
	>
    </div>
    <div class="input-group mb-3">
      <span class="input-group-text">Background color</span>
      <input
	type="color"
	class="form-control"
	v-model="newTagForm.bgColor"
	>
    </div>
  </form>
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
