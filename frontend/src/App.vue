<template>
  <div id="app-container">
    <header class="app-header">
        <h1>
          <img src="/portseido_logo_no_text.svg" alt="portfolio tracker" class="app-logo">
          portfolio tracker
        </h1>
        <div v-if="isAuthenticated" class="account-menu-wrapper">
          <button 
            @click="isMenuOpen = !isMenuOpen" 
            class="account-btn"
            :class="{ 'active': isMenuOpen }"
          >
            Account
            <span class="arrow" :class="{ 'open': isMenuOpen }">▿</span>
          </button>
          <div v-if="isMenuOpen" class="dropdown-menu">
            <div class="user-display">{{ userName }}</div>
            <div class="menu-divider"></div>
            <a href="#" class="menu-item" @click.prevent="isMenuOpen = false">Profile</a>
            <a href="#" class="menu-item logout" @click.prevent="handleLogout">Sign out</a>
          </div>
        </div>
        <AuthForm v-else @login-success="handleLoginSuccess" /> 
    </header>
    <WebSocketClient v-if="isAuthenticated" />
    <div v-if="isAuthenticated" class="portfolio-manager">
        <div class="portfolio-list-area">
          <div v-if="showCreatePortfolio==false" >
            <button 
                @click="showCreatePortfolio = !showCreatePortfolio" 
                class="action-btn" 
                style="margin-bottom: 15px;"
            >
              <img src="/add-symbol.svg" alt="Refresh" class="refresh-icon" />
            </button>
          </div>
            <div v-if="showCreatePortfolio" class="add-stock-area" style="padding: 15px; margin-bottom: 15px;">
                <CreatePortfolioForm 
                  @portfolio-created="refreshPortfolioList" 
                  @close="showCreatePortfolio = false" />
            </div>
            <PortfolioList 
                :key="portfolioListKey"
                :selected-portfolio-id="selectedPortfolioId"
                @select-portfolio="selectPortfolio"
                @portfolio-deleted="refreshPortfolioList"
            />
        </div>
        <div class="portfolio-details-area" v-if="selectedPortfolioId !== null">
          <PortfolioValuation 
                  :key="valuationKey" 
                  :portfolio-id="selectedPortfolioId"
                  :is-add-form-visible="showAddStockForm"         
                  @toggle-add-stock="toggleAddStockForm" />
          <SentimentForm 
                :ticker="'AAPL'"
                class="sentiment-analysis-area"
          />
          <div v-if="showAddStockForm" class="add-stock-area">
          <AddStockForm 
              :portfolio-id="selectedPortfolioId"
              :portfolio-name="selectedPortfolioName"
              @stock-added="refreshValuationData"
              @close="showAddStockForm = false"
          />
          </div>
        </div>
        <div v-else class="info-message" style="grid-column: 1 / -1; text-align: center;">
            Select a portfolio from the list or create a new one to view details and actions.
        </div>
    </div>
    <div v-else class="info-message">
        tomek
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { jwtDecode } from 'jwt-decode'
import AuthForm from './components/AuthForm.vue'
import CreatePortfolioForm from './components/CreatePortfolioForm.vue'
import PortfolioList from './components/PortfolioList.vue'
import AddStockForm from './components/AddStockForm.vue'
import PortfolioValuation from './components/PortfolioValuation.vue'
import WebSocketClient from './components/WebSocketClient.vue'
import SentimentForm from './components/SentimentForm.vue'

export default defineComponent({
  name: 'App',
  components: {
    AuthForm,
    CreatePortfolioForm,
    PortfolioList,
    AddStockForm,
    PortfolioValuation,
    WebSocketClient,
    SentimentForm
  },
  setup() {
    const isAuthenticated = ref(false)
    const selectedPortfolioId = ref<number | null>(null)
    const selectedPortfolioName = ref<string | null>(null)
    const portfolioListKey = ref(0)
    const valuationKey = ref(0)
    const isMenuOpen = ref(false)
    const userName = ref('john doe')
    const showCreatePortfolio = ref(false)
    const showAddStockForm = ref(false)

    const checkAuthStatus = () => {
      isAuthenticated.value = !!localStorage.getItem('access_token')
    }

    // -- On login events --
    const handleLoginSuccess = () => {

      // Used once successful login emited

      isAuthenticated.value = true
      showCreatePortfolio.value = false
      showAddStockForm.value = false
      
      // after logging in - force the wallet list to refresh
      const token = localStorage.getItem('access_token')
      if (token) {
          try {
              const decodedToken: { sub: string } = jwtDecode(token);
              // backend doesnt send user name for now - use user id Account box
              userName.value = 'ID: ' + decodedToken.sub

          } catch (e) {
              console.error("Token decoding error:", e)
              // userName.value = 'Guest'
          }
      }
      portfolioListKey.value++
    }   
    const handleLogout = () => {

      // Used after user log out

      localStorage.removeItem('access_token')
      isAuthenticated.value = false
      selectedPortfolioId.value = null
      selectedPortfolioName.value = null
      isMenuOpen.value = false
      showCreatePortfolio.value = false
      showAddStockForm.value = false
      
      // reload to force clean app state after log out
      window.location.reload() 

    }
    
    // -- Refresh data --
    const refreshPortfolioList = () => {

      // Used after ADDING/REMOVING WALLET

      portfolioListKey.value++
      
      // Reset details view after portfolio deletion
      selectedPortfolioId.value = null
      selectedPortfolioName.value = null
      showAddStockForm.value = false
      showCreatePortfolio.value = false

    }
    const refreshValuationData = () => {

      // Used after ADDING/REMOVING SHARES

      valuationKey.value++
      showAddStockForm.value = false

    }
    
    // -- Selection logic --
    const selectPortfolio = (id: number, name: string) => {
      
      // Used when switching porfolios

      selectedPortfolioId.value = id
      selectedPortfolioName.value = name
      // close the shares add form when switching portfolios
      showAddStockForm.value = false

    }
    const toggleAddStockForm = () => {

      // Shows / hides Add Stock Form

      showAddStockForm.value = !showAddStockForm.value

    }

    onMounted(() => {
            checkAuthStatus()
            // call token reading logic when loading the page if logged in
            if (localStorage.getItem('access_token')) {
                handleLoginSuccess()
            }

        })

   

    return {
      isAuthenticated,
      isMenuOpen,
      userName,
      selectedPortfolioId,
      selectedPortfolioName,
      portfolioListKey,
      valuationKey,
      showCreatePortfolio,
      showAddStockForm,
      handleLoginSuccess,
      handleLogout,
      selectPortfolio,
      refreshPortfolioList,
      refreshValuationData,
      toggleAddStockForm
    }
  },
})
</script>