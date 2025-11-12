<template>
  <div class="valuation-container">
    <div v-if="loading" class="info-message">Loading...</div>
    <div v-else-if="error" class="info-message error">{{ error }}</div>
    
    <div v-else-if="valuationData">
      <div v-if="isAddFormVisible==false" class="action-buttons-container"> 
        <button 
          @click="handleToggle" 
          class="add-stock-corner-btn"
          :class="{'close-icon-btn': isAddFormVisible}">
          <img src="/add-symbol.svg" alt="Refresh" class="refresh-icon" />
        </button>
        <button @click="handleRefreshValuation" class="refresh-btn" :disabled="loading">
          <span v-if="loading">Loading...</span>
          <span v-else>
            <img src="/icons8-refresh.svg" alt="Refresh" class="refresh-icon" />
          </span>
        </button>
      </div>

      
      <h2></h2>
      
    <div class="total-value-container">
      <span class="total-value" :class="totalFlash">{{ formatCurrency(valuationData.total_market_value) }}</span>
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
              <img v-if="stock.logo_url" :src="stock.logo_url" :alt="stock.ticker" class="company-logo" loading="lazy"/>
              <div class="ticker-info">
                <strong>{{ stock.ticker }}</strong>
                <span class="company-name">{{ stock.company_name }}</span>
              </div>
            </td>
            <td>{{ parseFloat(stock.shares).toFixed(2)}}</td>
            <td>{{ formatCurrency(stock.purchase_price) }}</td>
            <td :class="stock.flash">{{ formatCurrency(stock.current_price) }}</td>
            <td :class="stock.flash">{{ formatCurrency(stock.market_value) }}</td>
            <td :class="stock.profit_loss > 0 ? 'profit' : 'loss'">{{ formatCurrency(stock.profit_loss) }}</td>
            <td><button @click="deleteStock(stock.id)" class="delete-btn">Delete</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, getCurrentInstance, onMounted, onUnmounted } from 'vue'

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
  flash?: string
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
    const totalFlash = ref('')

    const formatCurrency = (value: number | string | null): string => {
        if (value === null) return 'N/A'
        const num = typeof value === 'string' ? parseFloat(value) : value
        return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'USD' }).format(num)
    }
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
    }
    const handleToggle = () => {
        emit('toggle-add-stock')
    }
    const handleRefreshValuation = () => {
      if (props.portfolioId) {
        fetchValuation(props.portfolioId)
      }
    }
    
    const updateTablePrice = (event: CustomEvent) => {
        const update = event.detail

        if (!valuationData.value) {
            return
        }
        
        const newPrice = update.price
        const stockIndex = valuationData.value.stocks.findIndex(s => s.ticker === update.ticker)
        
        if (stockIndex > -1) {
            
            const stock: StockValuation = valuationData.value.stocks[stockIndex]!
            const oldTotal = valuationData.value!.total_market_value

            // Zabezpieczenie przed użyciem null/undefined
            const oldPrice = stock.current_price !== null ? stock.current_price : 0
            let flashClass = ''
            
            if (newPrice > oldPrice) {
                flashClass = 'flash-up'
            } else if (newPrice < oldPrice) {
                flashClass = 'flash-down'
            }

          // Aktualizacja cen
          stock.current_price = newPrice
          
          // Przeliczenie wartości (używając nowej ceny)
          const shares = parseFloat(stock.shares)
          const purchasePrice = parseFloat(stock.purchase_price)
          
          stock.market_value = newPrice * shares
          stock.profit_loss = (stock.market_value - (purchasePrice * shares))
          
          // Wprowadzenie i usunięcie klasy flash
          stock.flash = flashClass

          setTimeout(() => {
              stock.flash = ''; // Usuń klasę flash po 1 sekundzie
          }, 1000)          
          
                  let newTotal = 0
        valuationData.value.stocks.forEach(s => {
            newTotal += s.market_value
        })

        valuationData.value.total_market_value = newTotal

        let totalFlashClass = '';
        if (newTotal > oldTotal) {
            totalFlashClass = 'flash-up-total';
        } else if (newTotal < oldTotal) {
            totalFlashClass = 'flash-down-total';
        }

        totalFlash.value = totalFlashClass

        setTimeout(() => {
            totalFlash.value = '';
        }, 1000)

        }


    }
    
    watch(() => props.portfolioId, (newId) => {
      if (newId) {
        fetchValuation(newId)
      }
    }, { immediate: true })

    onMounted(() => {
            window.addEventListener('priceUpdated', updateTablePrice as EventListener);
            fetchValuation(props.portfolioId);
    })

    onUnmounted(() => {
            window.removeEventListener('priceUpdated', updateTablePrice as EventListener);
    })

    return {
      valuationData,
      loading,
      error,
      totalFlash,
      formatCurrency,
      deleteStock,
      handleToggle,
      handleRefreshValuation
    };
  },
});
</script>