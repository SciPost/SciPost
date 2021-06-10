<template>
<div class="row">
  <div class="col-8">
    In child: {{ totalRows }} {{ perPage }} {{ currentPage }} {{ paginatorButtonData }}
    <nav aria-label="navigation">
      <ul class="pagination justify-content-center">
	<li v-for="pagenr in paginatorButtonData" class="page-item">
	  <span v-if="pagenr > 0">
	    <a class="page-link" :class="{ active: pagenr === currentPage }" @click="$emit('set-current-page', pagenr)">{{ pagenr }}</a>
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
	  <label class="btn btn-sm btn-outline-primary" :for="'btnRadioperPage-' + option">{{ option }}</label>
	</div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import { ref, computed } from '@vue/composition-api'

export default {
    name: 'sp-pagination',
    props: {
	totalRows: {
	    type: Number,
	    required: true
	},
	perPage: {
	    type: Number,
	    required: true
	},
	currentPage: {
	    type: Number,
	    required: true
	}
    },
    setup(props) {
	const perPageOptions = ref([8, 16, 32, 64])

	const paginatorButtonData = computed(() => {
	    var maxPageNr = Math.max(1, Math.ceil(props.totalRows.value/props.perPage.value))
	    let buttonData = [1,]
	    if (props.currentPage.value > 4) buttonData.push(0)
	    if (props.currentPage.value > 3) buttonData.push(props.currentPage.value - 2)
	    if (props.currentPage.value > 2) buttonData.push(props.currentPage.value - 1)
	    if (props.currentPage.value > 1) buttonData.push(props.currentPage.value)
	    if (props.currentPage.value < maxPageNr - 2) buttonData.push(props.currentPage.value + 1)
	    if (props.currentPage.value < maxPageNr - 3) buttonData.push(props.currentPage.value + 2)
	    if (props.currentPage.value < maxPageNr - 4) buttonData.push(0)
	    if (props.currentPage.value < maxPageNr) buttonData.push(maxPageNr)
	    return buttonData
	})

	return {
	    perPageOptions,
	    paginatorButtonData,
	}
    }
}
</script>
