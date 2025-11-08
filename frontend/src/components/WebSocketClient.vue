<template>
    <div v-if="notification" class="live-notification" @click="clearNotification">
        🔔 POWIADOMIENIE: {{ notification }}
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, watch } from 'vue';
import { jwtDecode } from 'jwt-decode';

export default defineComponent({
    name: 'WebSocketClient',
    setup() {
        const socket = ref<WebSocket | null>(null);
        const notification = ref<string | null>(null);
        const userId = ref<string | null>(null);
        
        // Adres Brokera (dostępny dla front-endu)
        const WS_URL = 'ws://localhost:8001/'; 
        
        const connectWebSocket = () => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                // Jeśli brak tokenu, nie łączymy się
                return;
            }

            try {
                const decodedToken: { sub: string } = jwtDecode(token);
                userId.value = decodedToken.sub; // Pobierz ID użytkownika
                
                // 1. Otwarcie połączenia
                socket.value = new WebSocket(WS_URL);

                socket.value.onopen = () => {
                    console.log('WebSocket: Połączono z Brokerem!');
                    
                    // 2. Rejestracja użytkownika (WYMAGANA PRZEZ BROKERA)
                    socket.value?.send(JSON.stringify({
                        user_id: userId.value,
                        type: 'REGISTER'
                    }));
                };

                socket.value.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'STOCK_ADDED') {
                        // Odbieranie powiadomienia od Brokera
                        notification.value = data.content; 
                    }
                    console.log('Odebrano wiadomość z WebSockets:', data);
                };

                socket.value.onclose = (event) => {
                    console.log('WebSocket: Rozłączono.', event.code, event.reason);
                    // Opcjonalnie: automatyczne ponawianie połączenia
                };

            } catch (e) {
                console.error("WebSocket: Nie udało się połączyć/dekodować tokenu.", e);
            }
        };

        const disconnectWebSocket = () => {
            if (socket.value) {
                socket.value.close();
                socket.value = null;
            }
        };

        const clearNotification = () => {
            notification.value = null;
        };

        // Łączenie przy montowaniu
        onMounted(connectWebSocket);
        
        // Rozłączanie przy demontowaniu komponentu (np. przy wylogowaniu)
        onUnmounted(disconnectWebSocket); 
        
        // Ponowne łączenie, jeśli token się zmienił/pojawił
        watch(() => localStorage.getItem('access_token'), (newToken) => {
            if (newToken && !socket.value) {
                connectWebSocket();
            } else if (!newToken && socket.value) {
                disconnectWebSocket();
            }
        });

        return {
            notification,
            clearNotification,
        };
    },
});
</script>