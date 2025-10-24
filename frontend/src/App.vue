<template>
  <div id="app-container">
    <h1>Portfel Inwestycyjny</h1>
    
    <button v-if="isAuthenticated" @click="handleLogout" class="logout-btn">
      Wyloguj
    </button>
    
    <AuthForm v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
    
    <hr>
    
    <div v-if="isAuthenticated">
      <CreatePortfolioForm />
    </div>
    <div v-else-if="!isAuthenticated" class="info-message">
      Proszę się zalogować, aby uzyskać dostęp.
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import AuthForm from './components/AuthForm.vue';
import CreatePortfolioForm from './components/CreatePortfolioForm.vue';

export default defineComponent({
  name: 'App',
  components: {
    AuthForm,
    CreatePortfolioForm, 
  },
  setup() {
    const isAuthenticated = ref(false);

    // FUNKCJA SPRAWDZAJĄCA, CZY TOKEN ISTNIEJE
    const checkAuthStatus = () => {
      // Jeśli token jest w localStorage, ustaw stan na true
      isAuthenticated.value = !!localStorage.getItem('access_token')
    };

    // 1. Sprawdzamy status natychmiast po załadowaniu komponentu
    onMounted(checkAuthStatus); 
    // ^ TO JEST KLUCZOWE, ABY APLIKACJA WIEDZIAŁA, ŻE JESTEŚ ZALOGOWANY PO ODŚWIEŻENIU STRONY

    // 2. Metoda do aktualizacji stanu po pomyślnym zalogowaniu (emit z AuthForm)
    const handleLoginSuccess = () => {
      isAuthenticated.value = true;
    };
    
    // 3. Metoda do wylogowania (usuwanie tokenu)
    const handleLogout = () => {
      localStorage.removeItem('access_token')
      isAuthenticated.value = false;
    };

    return {
      isAuthenticated,
      handleLoginSuccess,
      handleLogout, // Dodajemy funkcję do obsługi wylogowania
    }
  },
})
</script>