<template>
  <h1>Portfel Inwestycyjny</h1>
  <AuthForm />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import AuthForm from './components/AuthForm.vue'

export default defineComponent({
  name: 'App',
  components: {
    AuthForm,
  },
})
</script>