<template>
  <div class="sentiment-form-container">
    <button class="close-top-right" @click="$emit('close')">✕</button>
<div class="sentiment-header"> 
        
        <img 
            src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/google-gemini.svg" 
            alt="Google Gemini Logo" 
            class="gemini-logo" 
            loading="lazy"
        />
        
        <div class="header-details">
            <img 
                v-if="logoUrl" 
                :src="logoUrl" 
                :alt="ticker" 
                class="sentiment-icon-big" 
                loading="lazy"
            />
            <h3>Sentiment Analysis</h3>
        </div>
    </div>

    <div class="mode-manual">
        <textarea 
        v-model="manualText" 
        :placeholder="'Paste ' + ticker + ' news headlines or articles for analysis'"
        ></textarea>
        <button @click="triggerManualAnalysis" :disabled="!manualText.length" class="action-btn manual-btn">
            Submit
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
        logoUrl: { type: String, default: '' },
    },
    emits: ['close'],
    setup(props) {
        const manualText = ref('')
        const loading = ref(false)
        const message = ref('')
        const isSuccess = ref(false)

        const instance = getCurrentInstance();
        const $api = instance?.appContext.config.globalProperties.$api

        const sendAnalysisRequest = async (endpoint: string, data: object = {}) => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                message.value = 'Error: Unregistered user.';
                return;
            }
            
            loading.value = true;
            

            try {
                const response = await $api.post(endpoint, data, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                isSuccess.value = true;
                message.value = response.data.msg;
            } catch (error: any) {
                isSuccess.value = false;
                message.value = error.response?.data?.msg || 'Error connecting to the Gemini AI service';
            } finally {
                loading.value = false;
            }
        };

        const triggerAutomaticAnalysis = () => {
            sendAnalysisRequest(`/stock/${props.ticker}/analyze`);
        };
        
        const triggerManualAnalysis = () => {
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