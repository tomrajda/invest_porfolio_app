<template>
  <div class="auth-container">
    <h2>{{ isLogin ? 'Login' : 'Register' }}</h2>

    <form @submit.prevent="handleSubmit" class="login-form">
      <input type="text" v-model="username" placeholder="Username" required class="login-input"/>
      <input type="password" v-model="password" placeholder="Passwod" required class="login-input"/>
      
      <button type="submit" class="login-submit-btn">{{ isLogin ? 'Log in' : 'Register' }}</button>
    </form>

    <p @click="isLogin = !isLogin" class="toggle-mode">
      {{ isLogin ? 'Dont have an account? Sign up.' : 'Already have an account? Log in.' }}
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
    const instance = getCurrentInstance()
    const $api = instance?.appContext.config.globalProperties.$api

    const handleSubmit = async () => {
      message.value = ''
      const endpoint = isLogin.value ? '/auth/login' : '/auth/register'
      
      try {
        const response = await $api.post(endpoint, {
          username: username.value,
          password: password.value
        });

        isSuccess.value = true
        
        if (isLogin.value) {
          // log in success: save TOKEN
          const token = response.data.access_token
          localStorage.setItem('access_token', token)
          message.value = 'Successfully logged in!'
          
          emit('login-success')
          // to do: ADD HERE REDIRECTION
        } else {
          // registration success
          message.value = 'Registration successful!'
          isLogin.value = true // switch to login MODE
        }
      
      username.value = ''
      password.value = ''
      
      } catch (error: any) {
        isSuccess.value = false;
        // backend error handling (i.e. 401, 409)
        if (error.response) {
          message.value = `Error: ${error.response.data.msg || error.response.statusText}`
        } else {
          message.value = 'A network error has occurred.'
        }
      }
    }

    return {
      username,
      password,
      isLogin,
      message,
      isSuccess,
      handleSubmit,
    }
  },
})
</script>