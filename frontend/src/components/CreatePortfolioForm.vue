<template>
  <div class="portfolio-form-container">
    <h3>Utwórz nowy portfel</h3>
    <form @submit.prevent="createPortfolio">
      <input type="text" v-model="portfolioName" placeholder="Nazwa portfela" required />
      <button type="submit" :disabled="!authToken">Utwórz</button>
    </form>
    
    <p v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">{{ message }}</p>
    
    <div v-if="!authToken" class="error">
      Musisz być zalogowany, aby tworzyć portfele.
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance, onMounted } from 'vue'

export default defineComponent({
  name: 'CreatePortfolioForm',
  emits: ['portfolio-created'],
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
        message.value = 'Błąd: Token autoryzacji jest nieobecny. Zaloguj się ponownie.'
        isSuccess.value = false
        return;
      }

      message.value = 'Tworzenie...'

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
        message.value = `Sukces! Portfel '${response.data.name}' (ID: ${response.data.id}) utworzony.`
        portfolioName.value = '' // clear field
        emit('portfolio-created')

      } catch (error: any) {
        isSuccess.value = false;
        if (error.response) {
          message.value = `Błąd: ${error.response.data.msg || error.response.statusText}`
        } else {
          message.value = 'Błąd sieci. Sprawdź backend.'
        }
      }
    };

    return {
      portfolioName,
      message,
      isSuccess,
      authToken,
      createPortfolio,
    };
  },
});
</script>