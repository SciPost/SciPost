<template>
<div class="row m-1">
  <div class="col-md-1">
    {{ subsidy.organization.country }}
  </div>
  <div class="col-md-3">
    <a
      :href="subsidy.organization.url"
      target="_blank"
      rel="nofollow"
      >{{ subsidy.organization.name }}
    </a>
  </div>
  <div class="col-md-3">
    <a
      :href="subsidy.url"
      target="blank"
      rel="nofollow"
      >
      {{ subsidy.subsidy_type }}
    </a>
  </div>
  <div class="col-md-3">
    {{ subsidy.date }}&nbsp;--&nbsp;{{ subsidy.date_until }}
  </div>
  <div class="col-md-2">
    <div class="float-end">{{ subsidy.amount }}</div>
  </div>
</div>
</template>

<script>
export default {
    name: "subsidy-fin-admin-row-details",
    props: {
	subsidy: {
	    type: Object,
	    required: true
	}
    }
}
</script>
