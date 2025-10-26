<template>
  <div id="app-container">
    <h1>Portfel Inwestycyjny</h1>

    <AuthForm v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
    <button v-else @click="handleLogout" class="logout-btn">Wyloguj</button>
    
    <hr>
    
    <div v-if="isAuthenticated" class="portfolio-manager">
      
      <CreatePortfolioForm @portfolio-created="refreshPortfolioList" />
      
      <hr>

      <PortfolioList 
      :key="portfolioListKey" :selected-portfolio-id="selectedPortfolioId"
      @select-portfolio="selectPortfolio" @portfolio-deleted="refreshPortfolioList"
      />
      
      
      <div v-if="selectedPortfolioId !== null">
        <!-- <h2>Aktywny Portfel: {{ selectedPortfolioName }}</h2> -->
        <AddStockForm 
          :portfolio-id="selectedPortfolioId" 
          :portfolio-name="selectedPortfolioName" 
          @stock-added="refreshValuationData"/>
        <PortfolioValuation :key="valuationKey" :portfolio-id="selectedPortfolioId" />
      </div>
      <div v-else class="info-message">Wybierz portfel z listy, aby dodać akcje.</div>
    </div>
    <div v-else class="info-message">Proszę się zalogować, aby uzyskać dostęp.</div>

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