<template>
  <div id="app-container">
    
    <header class="app-header">
        <h1>
          <img src="/portseido_logo_no_text.svg" alt="Logo Portfela" class="app-logo">
          portfolio tracker
        </h1>
        
        <div v-if="isAuthenticated" class="account-menu-wrapper" @mouseleave="isMenuOpen = false">
            <button @click="isMenuOpen = !isMenuOpen" class="account-btn" @mouseover="isMenuOpen = true">
                Account ▿
            </button>
            
            <div v-if="isMenuOpen" class="dropdown-menu">
                <div class="user-display">{{ userName }}</div>
                <div class="menu-divider"></div>
                <a href="#" class="menu-item" @click.prevent="isMenuOpen = false">Profile (Mock)</a>
                <a href="#" class="menu-item logout" @click.prevent="handleLogout">Sign out</a>
            </div>
        </div>
        
        <AuthForm v-else @login-success="handleLoginSuccess" /> 
    </header>

    <div v-if="isAuthenticated" class="portfolio-manager">
      
        <div class="portfolio-list-area">
          
          <div v-if="showCreatePortfolio==false" >
            <button 
                @click="showCreatePortfolio = !showCreatePortfolio" 
                class="action-btn" 
                style="margin-bottom: 15px;"
            >
              +
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
            Wybierz portfel z listy lub utwórz nowy, aby wyświetlić szczegóły i akcje.
        </div>

    </div>
    <div v-else class="info-message">
        Proszę się zalogować, aby uzyskać dostęp do panelu inwestycyjnego.
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
    const isMenuOpen = ref(false)
    const userName = ref('Admin')
    const showCreatePortfolio = ref(false)
    const showAddStockForm = ref(false)

    const checkAuthStatus = () => {
      isAuthenticated.value = !!localStorage.getItem('access_token')
    };

    const handleLoginSuccess = () => {
      isAuthenticated.value = true
      showCreatePortfolio.value = false
      showAddStockForm.value = false
      // Po zalogowaniu wymuszamy odświeżenie listy portfeli

            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    const decodedToken: { sub: string } = jwtDecode(token);
                    // Twoje tokeny przechowują 'sub' (subject) jako ID.
                    
                    // UWAGA: Ponieważ backend nie wysyła nazwy, używamy ID jako mocka,
                    // dopóki nie dodamy endpointu /user/me do pobrania nazwy
                    userName.value = 'User ID: ' + decodedToken.sub; 

                } catch (e) {
                    console.error("Błąd dekodowania tokenu:", e);
                    userName.value = 'Gość';
                }
            }
            portfolioListKey.value++;
    };
    
    const handleLogout = () => {
      localStorage.removeItem('access_token')
      isAuthenticated.value = false
      selectedPortfolioId.value = null
      selectedPortfolioName.value = null
      isMenuOpen.value = false
      showCreatePortfolio.value = false
      showAddStockForm.value = false
      // Używamy reload, aby wymusić czysty stan aplikacji po wylogowaniu
      window.location.reload() 
    };
    
    // -------------------------------------------------------------------
    // FUNKCJE ODŚWIEŻANIA (ZGODNE Z TWOIM ZAMIARZEM)
    // -------------------------------------------------------------------

    const refreshPortfolioList = () => {
        // Używane po DODANIU/USUNIĘCIU PORTFELA
        portfolioListKey.value++
        // Resetuje widok szczegółów po usunięciu portfela
        selectedPortfolioId.value = null; 
        selectedPortfolioName.value = null;
        showAddStockForm.value = false;
        showCreatePortfolio.value = false;
    }

    const refreshValuationData = () => {
      // Używane po DODANIU/USUNIĘCIU AKCJI
      valuationKey.value++
      showAddStockForm.value = false // Zamykamy formularz po dodaniu akcji
    };
    
    // -------------------------------------------------------------------
    // LOGIKA WYBORU PORTFELA
    // -------------------------------------------------------------------

    const selectPortfolio = (id: number, name: string) => {
      selectedPortfolioId.value = id
      selectedPortfolioName.value = name
      // Zamykamy formularz dodawania akcji przy przełączaniu portfela
      showAddStockForm.value = false
    }
    const toggleAddStockForm = () => {
      showAddStockForm.value = !showAddStockForm.value
    }
    onMounted(() => {
            checkAuthStatus();
            // Wywołaj logikę odczytu tokenu przy ładowaniu strony, jeśli zalogowano
            if (localStorage.getItem('access_token')) {
                handleLoginSuccess();
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