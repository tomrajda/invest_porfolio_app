<template>
  <div class="sentiment-form-container">
    <h3>Analiza Nastrojów AI (Gemini)</h3>
    
    <div class="mode-auto">
        <button @click="triggerAutomaticAnalysis" :disabled="loading" class="action-btn">
            {{ loading ? 'Analizowanie...' : '🤖 Automatyczna Analiza Tickers' }}
        </button>
    </div>

    <div class="mode-manual">
        <textarea v-model="manualText" placeholder="Wklej nagłówki newsów lub artykuł do analizy..."></textarea>
        <button @click="triggerManualAnalysis" :disabled="!manualText.length" class="action-btn manual-btn">
            Analizuj Wklejony Tekst
        </button>
    </div>

    <p v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">{{ message }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance } from 'vue';

export default defineComponent({
    name: 'SentimentForm',
    props: {
        ticker: { type: String, required: true },
    },
    setup(props) {
        const manualText = ref('');
        const loading = ref(false);
        const message = ref('');
        const isSuccess = ref(false);

        const instance = getCurrentInstance();
        const $api = instance?.appContext.config.globalProperties.$api;

        const sendAnalysisRequest = async (endpoint: string, data: object = {}) => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                message.value = 'Błąd: Użytkownik niezalogowany.';
                return;
            }
            
            loading.value = true;
            message.value = 'Wysyłanie do AI... Może to potrwać kilkanaście sekund.';

            try {
                const response = await $api.post(endpoint, data, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                isSuccess.value = true;
                message.value = response.data.msg;
            } catch (error: any) {
                isSuccess.value = false;
                message.value = error.response?.data?.msg || 'Błąd połączenia z serwisem AI.';
            } finally {
                loading.value = false;
            }
        };

        const triggerAutomaticAnalysis = () => {
            // Tryb 1: Używa tickera do pobrania newsów w Flasku
            sendAnalysisRequest(`/stock/${props.ticker}/analyze`);
        };
        
        const triggerManualAnalysis = () => {
            // Tryb 2: Używa wklejonego tekstu
            sendAnalysisRequest(`/stock/${props.ticker}/analyze/manual`, { text_content: manualText.value });
        };

        return {
            manualText,
            loading,
            message,
            isSuccess,
            triggerAutomaticAnalysis,
            triggerManualAnalysis,
        };
    },
});
</script>