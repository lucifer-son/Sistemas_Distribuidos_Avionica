<template>
  <div class="col-12 col-md-6 col-xl-3">
    <article class="panel h-100">
      <div class="mb-3">
        <h2 class="h6 mb-1">{{ title }}</h2>
        <p class="text-secondary small mb-0">{{ subtitle }}</p>
      </div>

      <dl v-if="items.length > 0" class="data-list mb-0">
        <template v-for="item in items" :key="item.key">
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </template>
      </dl>

      <p v-else class="text-secondary mb-0">Aguardando dados.</p>
    </article>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    required: true
  },
  items: {
    type: Array,
    default: () => []
  }
});
</script>
