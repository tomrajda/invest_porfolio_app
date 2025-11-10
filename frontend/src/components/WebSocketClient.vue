<template>
    <div v-if="notification" class="live-notification" @click="clearNotification">
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
        
        // Broker address 
        const WS_URL = 'ws://localhost:8001';
        
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
                    
                    if (
                        data.type === 'STOCK_ADDED' || 
                        data.type === 'STOCK_DELETED' || 
                        data.type === 'PORTFOLIO_ADDED' ||
                        data.type == 'PORTFOLIO_DELETED' ||
                        data.type === 'PRICE_ALERT'
                    ) {
                        // notifcation from Broker
                        notification.value = data.content
                    }
                    else if (data.type === 'PRICE_UPDATE') { 
                        // Send message to Vue
                        window.dispatchEvent(new CustomEvent('priceUpdated', { detail: data }));
                    }
                    
                    console.log('Message received from WebSockets:', data)
                };

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
            notification.value = null
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
            notification,
            clearNotification,
        };
    },
});
</script>