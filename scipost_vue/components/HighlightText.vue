<template>
  <span v-html="highlightedText"></span>
</template>

<script>
import { ref, computed } from '@vue/composition-api'

export default {
    name: "highlight-text",
    props: {
	text: String,
	queries: {
	    type: Array,
	    default() {
		return [{ query: "", caseSensitive: false },]
	    }
	}
    },
    setup(props) {
	const highlightedText = computed(() => {
	    let tempText = props.text
	    props.queries.forEach( (query) => {
		if (query.query) {
		    tempText = tempText.replace(
			new RegExp(query.query, query.caseSensitive ? "g" : "ig"),
			function(match) {
			    return (`<mark>${match}</mark>`)
			})
		}
	    })
	    return tempText
	})
	return {
	    highlightedText
	}
    }
}
</script>
