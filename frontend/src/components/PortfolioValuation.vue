<template>
  <div class="valuation-container">
    <div v-if="loading" class="info-message">Ładowanie wyceny portfela...</div>
    <div v-else-if="error" class="info-message error">{{ error }}</div>
    
    <div v-else-if="valuationData">
      <h2>Wycena: {{ valuationData.portfolio_name }}</h2>
      
      <div class="summary">
        Całkowita Wartość Rynkowa: 
        <span class="total-value">{{ formatCurrency(valuationData.total_market_value) }}</span>
      </div>

      <table class="stocks-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Ilość</th>
            <th>Cena Zakupu</th>
            <th>Aktualna Cena</th>
            <th>Wartość Rynkowa</th>
            <th>Zysk/Strata</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in valuationData.stocks" :key="stock.id">
            <td>{{ stock.ticker }}</td>
            <td>{{ stock.shares }}</td>
            <td>{{ formatCurrency(stock.purchase_price) }}</td>
            <td>{{ formatCurrency(stock.current_price) }}</td>
            <td>{{ formatCurrency(stock.market_value) }}</td>
            <td :class="stock.profit_loss > 0 ? 'profit' : 'loss'">
              {{ formatCurrency(stock.profit_loss) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, getCurrentInstance } from 'vue';

interface StockValuation {
  id: number;
  ticker: string;
  shares: string;
  purchase_price: string;
  current_price: number | null;
  market_value: number;
  profit_loss: number;
}

interface PortfolioValuation {
  portfolio_name: string;
  stocks: StockValuation[];
  total_market_value: number;
}

export default defineComponent({
  name: 'PortfolioValuation',
  props: {
    portfolioId: { // Aktywny portfel
      type: Number,
      required: true,
    }
  },
  setup(props) {
    const valuationData = ref<PortfolioValuation | null>(null);
    const loading = ref(false);
    const error = ref('');

    const instance = getCurrentInstance();
    const $api = instance?.appContext.config.globalProperties.$api;

    const formatCurrency = (value: number | string | null): string => {
        if (value === null) return 'N/A';
        const num = typeof value === 'string' ? parseFloat(value) : value;
        return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'USD' }).format(num);
    };

    const fetchValuation = async (id: number) => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      
      loading.value = true;
      error.value = '';
      valuationData.value = null;

      try {
        const response = await $api.get(`/portfolios/${id}/valuation`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        valuationData.value = response.data;
      } catch (e: any) {
        error.value = e.response?.data?.msg || 'Nie udało się pobrać wyceny.';
      } finally {
        loading.value = false;
      }
    };
    
    // Używamy WATCH, aby reagować na zmianę prop-sa (zmianę aktywnego portfela)
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
    };
  },
});
</script>