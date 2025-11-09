<template>
  <div class="list-container">
    
    <div v-if="loading" class="info-message">Loading portfolios...</div>
    <div v-else-if="portfolios.length === 0" class="info-message error">
      You don't have any portfolios yet. Create one!
    </div>
    <ul v-else>
      <li 
        v-for="portfolio in portfolios" 
        :key="portfolio.id" 
        :class="{ 'selected': portfolio.id === selectedPortfolioId }"
        @click="$emit('select-portfolio', portfolio.id, portfolio.name)"
      >
        <div class="list-item-content"> <span class="portfolio-name">
              {{ portfolio.name }}
          </span>
            
          <button 
              @click.stop="confirmDelete(portfolio.id, portfolio.name)" 
              class="delete-portfolio-btn"
          >
            Delete
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, getCurrentInstance } from 'vue'

interface Portfolio {
  id: number
  name: string
}

export default defineComponent({
  name: 'PortfolioList',
  props: {
    selectedPortfolioId: {
      type: [Number, null], 
      default: null 
    }
  },
  emits: ['select-portfolio', 'portfolio-deleted'],
  setup(_,  { emit }) {
    const portfolios = ref<Portfolio[]>([])
    const loading = ref(false)

    const instance = getCurrentInstance()
    const $api = instance?.appContext.config.globalProperties.$api

    const fetchPortfolios = async () => {
      const token = localStorage.getItem('access_token')
      if (!token) return

      loading.value = true;
      try {
        const response = await $api.get('/portfolios', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        portfolios.value = response.data;

      } catch (error) {
        console.error('Porfolio loading error:', error)
      } finally {
        loading.value = false
      }
    }
    
    const deletePortfolio = async (portfolioId: number, portfolioName: string) => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        try {
            await $api.delete(`/portfolios/${portfolioId}`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            // send event to parent
            emit('portfolio-deleted'); 
                
            // alert(`Portfel '${portfolioName}' usunięty pomyślnie.`);

        } catch (error: any) {
                alert(error.response?.data?.msg || 'Error: Failed to delete wallet.')
            }
        };

    const confirmDelete = (id: number, name: string) => {
        if (confirm(
          `Are you sure you want to delete your wallet '${name}'?\n\nAll related stocks will be deleted!`)) {
                deletePortfolio(id, name);
            }
    };

    onMounted(fetchPortfolios)

    return {
      portfolios,
      loading,
      fetchPortfolios,
      confirmDelete,
    }
  },
})
</script>