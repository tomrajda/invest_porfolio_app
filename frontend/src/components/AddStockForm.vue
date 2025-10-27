<template>
  <div class="stock-form-container">
    <h3></h3>
    <form @submit.prevent="addStock">
      <input type="text" v-model="ticker" placeholder="Share ticker (i.e. AAPL)" required />
      <input type="number" v-model="shares" placeholder="Shares amount" required min="0.01" step="0.01" />
      <input type="number" v-model="purchasePrice" placeholder="Price per share" required min="0.01" step="0.01" />
      
      <button type="submit" :disabled="!portfolioId">Add share</button>
    </form>
    
    <p v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">{{ message }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance, watch } from 'vue';

export default defineComponent({
  name: 'AddStockForm',
  props: {
    portfolioId: {
      type: Number,
      required: true
    },
    portfolioName: {
        type: [String, null],
        required: true
    }
  },
  emits: ['stock-added'],
  setup(props, { emit }) {
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

      message.value = 'Adding stock...';

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

        // from Reset
        ticker.value = '';
        shares.value = 0;
        purchasePrice.value = 0;
        
        emit('stock-added')

      } catch (error: any) {
        isSuccess.value = false;
        message.value = `Error: ${error.response?.data?.msg || 'The stock could not be added.'}`;
      }
    };

    watch(() => props.portfolioId, (newId, oldId) => {
      
      if (newId !== oldId) {
        message.value = '';
      }
    });

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