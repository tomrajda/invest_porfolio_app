<template>
    <div v-if="notification" class="live-notification" :class="notificationClass" @click="clearNotification">
        🔔  {{ Array.isArray(notification) ? notification[0] : notification }}
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, watch } from 'vue'
import { jwtDecode } from 'jwt-decode'

export default defineComponent({
    name: 'WebSocketClient',
    setup() {
        
        const socket = ref<WebSocket | null>(null)
        const notification = ref<string | null>(null)
        const userId = ref<string | null>(null)
        const sentimentResult = ref<any>(null)
        const notificationClass = ref('')

        // Broker address 
        const WS_URL = 'ws://localhost:8001'
        
        const connectWebSocket = () => {
            const token = localStorage.getItem('access_token')
            if (!token) {
                return
            }

            try {
                const decodedToken: { sub: string } = jwtDecode(token)
                userId.value = decodedToken.sub
                
                // Open connection
                socket.value = new WebSocket(WS_URL)

                socket.value.onopen = () => {
                    console.log('WebSocket: Connected with Broker!')
                    
                    socket.value?.send(JSON.stringify({
                        user_id: userId.value,
                        type: 'REGISTER'
                    }))
                }

                socket.value.onmessage = (event) => {
                    const data = JSON.parse(event.data)
                    const type = data.type

                    if (type === 'SENTIMENT_READY') {
                        sentimentResult.value = data
                        notification.value = data.content
                        notificationClass.value = getAlertClass(data.sentiment)
                        localStorage.setItem('sentiment_result', JSON.stringify(data))
                        
                    } else if (
                        type === 'STOCK_ADDED' || 
                        type === 'STOCK_DELETED' || 
                        type === 'PORTFOLIO_ADDED' ||
                        type === 'PORTFOLIO_DELETED' ||
                        type === 'SENTIMENT_FAILED'
                    ) {
 
                        notification.value = data.content
                        
                        notificationClass.value = 'alert-info'
                        
                    } else if (type === 'PRICE_UPDATE') { 
                        window.dispatchEvent(new CustomEvent('priceUpdated', { detail: data }))
                    }
                    
         
                }

                socket.value.onclose = (event) => {
                    console.log('WebSocket: Disconnected.', event.code, event.reason)
                }

            } catch (e) {
                console.error("WebSocket: Cannot connect/decode token", e)
            }
        }

        const disconnectWebSocket = () => {
            if (socket.value) {
                socket.value.close()
                socket.value = null
            }
        }

        const clearNotification = () => {
            if (sentimentResult.value) {
                localStorage.setItem('last_sentiment_result', JSON.stringify(sentimentResult.value));
                sentimentResult.value = null;
                
                // SEND SIGNAL TO PARENT
                window.dispatchEvent(new CustomEvent('sentimentDisplayed')); 
            }
            notification.value = null
            notificationClass.value = ''
        }

        const getAlertClass = (sentiment: string) => {
            switch (sentiment) {
                case 'POSITIVE': return 'alert-positive'
                case 'NEGATIVE': return 'alert-negative'
                case 'NEUTRAL': return 'alert-neutral'
                default: return ''
            }
        }

        onMounted(connectWebSocket)
        onUnmounted(disconnectWebSocket)
        
        watch(() => localStorage.getItem('access_token'), (newToken) => {
            if (newToken && !socket.value) {
                connectWebSocket()
            } else if (!newToken && socket.value) {
                disconnectWebSocket()
            }
        })

        return {
            sentimentResult,
            notification,
            notificationClass,
            clearNotification,
        }
    },
})
</script>