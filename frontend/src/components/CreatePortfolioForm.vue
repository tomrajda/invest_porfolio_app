<template>
  <div class="portfolio-form-container">
    <div class="portfolio-form-container">
      <button class="close-top-right" @click="$emit('close')">✕</button>
    </div>
    <h3>Add portfolio</h3>
    <form @submit.prevent="createPortfolio">
      <input type="text" v-model="portfolioName" placeholder="Portfolio name" required />
      <button type="submit" :disabled="!authToken">Submit</button>
    </form>
    <p v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">{{ message }}</p>
    <div v-if="!authToken" class="error">
      You must be logged in to create portfolios.
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance, onMounted } from 'vue'

export default defineComponent({
  name: 'CreatePortfolioForm',
  emits: ['portfolio-created', 'close'],
  setup(_, { emit }) {
    const portfolioName = ref('')
    const message = ref('')
    const isSuccess = ref(false)
    const authToken = ref('')

    const instance = getCurrentInstance()
    const $api = instance?.appContext.config.globalProperties.$api

    onMounted(() => {
      // download token during loading of component
      const token = localStorage.getItem('access_token')
      if (token) {
        authToken.value = token
      }
    });

    const createPortfolio = async () => {
      if (!authToken.value) {
        message.value = 'Error: Authorization token is missing. Please log in again.'
        isSuccess.value = false
        return
      }

      message.value = 'Creating...'

      try {
        const response = await $api.post('/portfolios', 
          { name: portfolioName.value }, 
          {
            headers: {
              Authorization: `Bearer ${authToken.value}` // ADD TOKEN
            }
          }
        );

        isSuccess.value = true
        message.value = `Success! Wallet '${response.data.name}' (ID: ${response.data.id}) created.`
        
        setTimeout(() => {
            message.value = ''
            isSuccess.value = false
        }, 5000)
        
        portfolioName.value = '' // clear field
        emit('portfolio-created')

      } catch (error: any) {
        isSuccess.value = false
        if (error.response) {
          message.value = `Error: ${error.response.data.msg || error.response.statusText}`
        } else {
          message.value = 'Network error'
        }
      }
    };

    return {
      portfolioName,
      message,
      isSuccess,
      authToken,
      createPortfolio,
    }
  },
})
</script>