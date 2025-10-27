<template>
  <div id="app-container">
    
    <header class="app-header">
        <h1>portfolio tracker</h1>
        <button v-if="isAuthenticated" @click="handleLogout" class="logout-btn">
            Wyloguj
        </button>
    </header>

    <AuthForm v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
    
    <div v-else class="portfolio-manager">
      
      <div class="portfolio-list-area">
        <CreatePortfolioForm @portfolio-created="refreshPortfolioList" /> 
        
        <hr style="border-color: #4a4a6e; margin: 20px 0;">
        
        <PortfolioList 
          :key="portfolioListKey"
          :selected-portfolio-id="selectedPortfolioId"
          @select-portfolio="selectPortfolio"
          @portfolio-deleted="refreshPortfolioList"
        />
      </div>

      <div class="portfolio-details-area" v-if="selectedPortfolioId !== null">
        <PortfolioValuation :key="valuationKey" :portfolio-id="selectedPortfolioId" />
        
        <hr style="border-color: #4a4a6e; margin: 20px 0;">

        <div class="add-stock-area">
            <h2>Add stock</h2>
            <AddStockForm 
              :portfolio-id="selectedPortfolioId"
              :portfolio-name="selectedPortfolioName"
              @stock-added="refreshValuationData"
            />
        </div>
      </div>
      <div v-else class="info-message" style="grid-column: 1 / -1; text-align: center;">
          Wybierz portfel z listy lub utwórz nowy, aby wyświetlić szczegóły i akcje.
      </div>

    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import AuthForm from './components/AuthForm.vue';
import CreatePortfolioForm from './components/CreatePortfolioForm.vue'
import PortfolioList from './components/PortfolioList.vue'
import AddStockForm from './components/AddStockForm.vue'
import PortfolioValuation from './components/PortfolioValuation.vue'

export default defineComponent({
  name: 'App',
  components: {
    AuthForm,
    CreatePortfolioForm,
    PortfolioList,
    AddStockForm,
    PortfolioValuation
  },
  setup() {
    const isAuthenticated = ref(false)
    const selectedPortfolioId = ref<number | null>(null)
    const selectedPortfolioName = ref<string | null>(null)
    const portfolioListKey = ref(0)
    const valuationKey = ref(0)

    const checkAuthStatus = () => {
      isAuthenticated.value = !!localStorage.getItem('access_token')
    };

    const handleLoginSuccess = () => {
      isAuthenticated.value = true
    };
    
    const handleLogout = () => {
      localStorage.removeItem('access_token')
      isAuthenticated.value = false
      selectedPortfolioId.value = null
      selectedPortfolioName.value = null
    };
    
    const refreshPortfolioList = () => {
      portfolioListKey.value++
    }

    const refreshValuationData = () => {
      valuationKey.value++; 
    };
    
    const selectPortfolio = (id: number, name: string) => {
      selectedPortfolioId.value = id
      selectedPortfolioName.value = name
    }

    onMounted(checkAuthStatus)

    return {
      isAuthenticated,
      selectedPortfolioId,
      selectedPortfolioName,
      portfolioListKey,
      valuationKey,
      handleLoginSuccess,
      handleLogout,
      selectPortfolio,
      refreshPortfolioList,
      refreshValuationData
    }
  },
})
</script>