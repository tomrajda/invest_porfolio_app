<template>
  <div class="valuation-container">
    <div v-if="loading" class="info-message">loading...</div>
    <div v-else-if="error" class="info-message error">{{ error }}</div>
    
    <div v-else-if="valuationData">
      <div v-if="isAddFormVisible==false" > 
        <button 
          @click="handleToggle" 
          class="add-stock-corner-btn"
          :class="{'close-icon-btn': isAddFormVisible}">
          +
        </button>
      </div>

      
      <h2></h2>
      
    <div class="total-value-container">
      <span class="total-value">{{ formatCurrency(valuationData.total_market_value) }}</span>
    </div>

      <table class="stocks-table">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Amount</th>
            <th>Purchase price</th>
            <th>Current price</th>
            <th>Market value</th>
            <th>Profit/Loss</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in valuationData.stocks" :key="stock.id">
            <td class="ticker-cell">
              <img v-if="stock.logo_url" :src="stock.logo_url" :alt="stock.ticker" class="company-logo" />
              <div class="ticker-info">
                <strong>{{ stock.ticker }}</strong>
                <span class="company-name">{{ stock.company_name }}</span>
              </div>
            </td>
            <td>{{ stock.shares }}</td>
            <td>{{ formatCurrency(stock.purchase_price) }}</td>
            <td>{{ formatCurrency(stock.current_price) }}</td>
            <td>{{ formatCurrency(stock.market_value) }}</td>
            <td :class="stock.profit_loss > 0 ? 'profit' : 'loss'">
              {{ formatCurrency(stock.profit_loss) }}
            </td>
            <td>
              <button @click="deleteStock(stock.id)" class="delete-btn">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, getCurrentInstance } from 'vue'

interface StockValuation {
  id: number
  ticker: string
  shares: string
  purchase_price: string
  current_price: number | null
  market_value: number
  profit_loss: number
  logo_url: string
  company_name: string
}

interface PortfolioValuation {
  portfolio_name: string
  stocks: StockValuation[]
  total_market_value: number
}

export default defineComponent({
  name: 'PortfolioValuation',
  props: {
    portfolioId: { type: Number, required: true },
    isAddFormVisible: { type: Boolean, default: false }
  },
  emits: ['toggle-add-stock'],
  setup(props, { emit }) {
    const valuationData = ref<PortfolioValuation | null>(null)
    const loading = ref(false)
    const error = ref('')

    const instance = getCurrentInstance()
    const $api = instance?.appContext.config.globalProperties.$api

    const formatCurrency = (value: number | string | null): string => {
        if (value === null) return 'N/A'
        const num = typeof value === 'string' ? parseFloat(value) : value
        return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'USD' }).format(num)
    };

    const fetchValuation = async (id: number) => {
      const token = localStorage.getItem('access_token')
      if (!token) return;
      
      loading.value = true
      error.value = ''
      valuationData.value = null;

      try {
        const response = await $api.get(`/portfolios/${id}/valuation`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        valuationData.value = response.data
      } catch (e: any) {
        error.value = e.response?.data?.msg || 'The portfolio valuation could not be retrieved.'
      } finally {
        loading.value = false
      }
    }
    
    const deleteStock = async (stockId: number) => {
      if (!confirm(`Are you sure you want to delete action ID: ${stockId}?`)) {
        return;
      }
      
      const token = localStorage.getItem('access_token');
      if (!token || !props.portfolioId) return;

      try {
        await $api.delete(`/portfolios/${props.portfolioId}/stocks/${stockId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        // wymuszenie ponownego załadowania wyceny po usunięciu
        fetchValuation(props.portfolioId); 
        
      } catch (e: any) {
        alert(e.response?.data?.msg || 'The share could not be deleted.');
      }
    };
    const handleToggle = () => {
        emit('toggle-add-stock')
    }
    // use WATCH, aby reagować na zmianę prop-sa (zmianę aktywnego portfela)
    watch(() => props.portfolioId, (newId) => {
      if (newId) {
        fetchValuation(newId);
      }
    }, { immediate: true }); // immediate: true oznacza, że wywoła się od razu przy montowaniu

    return {
      valuationData,
      loading,
      error,
      formatCurrency,
      deleteStock,
      handleToggle
    };
  },
});
</script>