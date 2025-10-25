<template>
  <div class="stock-form-container">
    <h3>Dodaj Akcję do Portfela {{ portfolioId }}</h3>
    <form @submit.prevent="addStock">
      <input type="text" v-model="ticker" placeholder="Symbol akcji (np. AAPL)" required />
      <input type="number" v-model="shares" placeholder="Liczba akcji" required min="0.01" step="0.01" />
      <input type="number" v-model="purchasePrice" placeholder="Cena zakupu za akcję" required min="0.01" step="0.01" />
      
      <button type="submit" :disabled="!portfolioId">Dodaj Akcję</button>
    </form>
    
    <p v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">{{ message }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance } from 'vue';

export default defineComponent({
  name: 'AddStockForm',
  props: {
    portfolioId: { // Otrzymujemy ID aktywnego portfela z rodzica
      type: Number,
      required: true
    }
  },
  setup(props) {
    const ticker = ref('');
    const shares = ref(0);
    const purchasePrice = ref(0);
    const message = ref('');
    const isSuccess = ref(false);

    const instance = getCurrentInstance();
    const $api = instance?.appContext.config.globalProperties.$api;

    const addStock = async () => {
      const token = localStorage.getItem('access_token');
      if (!token || !props.portfolioId) return;

      message.value = 'Dodawanie akcji...';

      try {
        const response = await $api.post(`/portfolios/${props.portfolioId}/stocks`, 
          { 
            ticker: ticker.value,
            shares: shares.value,
            purchase_price: purchasePrice.value,
          }, 
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        isSuccess.value = true;
        message.value = response.data.msg;

        // Reset formularza
        ticker.value = '';
        shares.value = 0;
        purchasePrice.value = 0;

      } catch (error: any) {
        isSuccess.value = false;
        message.value = `Błąd: ${error.response?.data?.msg || 'Nie udało się dodać akcji.'}`;
      }
    };

    return {
      ticker,
      shares,
      purchasePrice,
      message,
      isSuccess,
      addStock,
    };
  },
});
</script>