<template>
  <div class="stock-form-container">
    <div class="stock-form-container">
    <button class="close-top-right" @click="$emit('close')">✕</button> 
    <h2>Add stock</h2>
    </div>
    <form @submit.prevent="addStock" class="form-row" >
      <input type="text" v-model="ticker" placeholder="Share ticker" required class="form-input"/>
      <input type="number" v-model="shares" placeholder="Shares amount" required min="0.01" step="0.01" class="form-input"/>
      <input type="number" v-model="purchasePrice" placeholder="Price per share" required min="0.01" step="0.01" class="form-input"/>
      <button type="submit" :disabled="!portfolioId" class="form-submit-btn">Submit</button>
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
  emits: ['stock-added', 'close'],
  setup(props, { emit }) {
    const ticker = ref('');
    const shares = ref<number | null>(null);
    const purchasePrice = ref<number | null>(null);
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
        shares.value = null;
        purchasePrice.value = null;
        
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