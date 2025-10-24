<template>
  <div class="auth-container">
    <h2>{{ isLogin ? 'Logowanie' : 'Rejestracja' }}</h2>
    
    <form @submit.prevent="handleSubmit">
      <input type="text" v-model="username" placeholder="Nazwa użytkownika" required />
      <input type="password" v-model="password" placeholder="Hasło" required />
      
      <button type="submit">{{ isLogin ? 'Zaloguj' : 'Zarejestruj' }}</button>
    </form>
    
    <p @click="isLogin = !isLogin" class="toggle-mode">
      {{ isLogin ? 'Nie masz konta? Zarejestruj się.' : 'Masz już konto? Zaloguj się.' }}
    </p>

    <div v-if="message" :class="{'success': isSuccess, 'error': !isSuccess}">
      {{ message }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, getCurrentInstance } from 'vue'

export default defineComponent({
  name: 'AuthForm',
  emits: ['login-success'],
  setup(_, { emit }) {
    // reactive variables for form state and view
    const username = ref('')
    const password = ref('')
    const isLogin = ref(true) // True: log in MODE, False: register MODE
    const message = ref('')
    const isSuccess = ref(false)

    // access to global API client
    const instance = getCurrentInstance();
    const $api = instance?.appContext.config.globalProperties.$api

    const handleSubmit = async () => {
      message.value = '';
      const endpoint = isLogin.value ? '/auth/login' : '/auth/register'
      
      try {
        const response = await $api.post(endpoint, {
          username: username.value,
          password: password.value
        });

        isSuccess.value = true;
        
        if (isLogin.value) {
          // log in success: save TOKEN
          const token = response.data.access_token
          localStorage.setItem('access_token', token)
          message.value = 'Zalogowano pomyślnie! Token zapisany.'
          
          emit('login-success')
          // to do: ADD HERE REDIRECTION
        } else {
          // registration success
          message.value = 'Rejestracja udana! Możesz się teraz zalogować.'
          isLogin.value = true; // switch to login MODE
        }
      
      username.value = '';
      password.value = '';
      
      } catch (error: any) {
        isSuccess.value = false;
        // backend error handling (i.e. 401, 409)
        if (error.response) {
          message.value = `Błąd: ${error.response.data.msg || error.response.statusText}`;
        } else {
          message.value = 'Wystąpił błąd sieci. Sprawdź, czy backend działa.';
        }
      }
    };

    return {
      username,
      password,
      isLogin,
      message,
      isSuccess,
      handleSubmit,
    };
  },
});
</script>