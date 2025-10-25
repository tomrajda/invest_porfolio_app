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
      @select-portfolio="selectPortfolio"
      />
      
      <div v-if="selectedPortfolioId !== null">
        <h2>Aktywny Portfel: {{ selectedPortfolioId }}</h2>
        <AddStockForm :portfolio-id="selectedPortfolioId" />
        <PortfolioValuation :portfolio-id="selectedPortfolioId" />
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
    const portfolioListKey = ref(0)

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
    };
    
    const refreshPortfolioList = () => {
      portfolioListKey.value++
    }
    
    const selectPortfolio = (id: number) => {
      selectedPortfolioId.value = id
    }

    onMounted(checkAuthStatus)

    return {
      isAuthenticated,
      selectedPortfolioId,
      portfolioListKey,
      handleLoginSuccess,
      handleLogout,
      selectPortfolio,
      refreshPortfolioList
    }
  },
})
</script>