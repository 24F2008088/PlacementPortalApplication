<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <!-- Added border-secondary for a cleaner dark mode look -->
    <div class="card shadow-lg p-4 bg-dark text-light border-secondary" style="width: 25rem;">
      <h3 class="text-center mb-4">{{ isRegistering ? 'Create Account' : 'Welcome Back' }}</h3>
      
      <!-- Alerts -->
      <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input type="text" class="form-control" v-model="username" required>
        </div>

        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" class="form-control" v-model="password" required>
        </div>

        <div v-if="isRegistering" class="mb-4">
          <label class="form-label">I am a:</label>
          <select class="form-select" v-model="role">
            <option value="student">Student</option>
            <option value="company">Company</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <button type="submit" class="btn btn-primary w-100 mb-3">
          {{ isRegistering ? 'Register' : 'Log In' }}
        </button>
      </form>

      <div class="text-center">
        <button class="btn btn-link text-decoration-none" @click="toggleMode">
          {{ isRegistering ? 'Already have an account? Log in' : 'Need an account? Register' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const isRegistering = ref(false)
const username = ref('')
const password = ref('')
const role = ref('student')
const errorMessage = ref('')
const successMessage = ref('')

const router = useRouter()
const API_URL = 'http://127.0.0.1:5000/api'

const toggleMode = () => {
  isRegistering.value = !isRegistering.value
  errorMessage.value = ''
  successMessage.value = ''
}

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  try {
    if (isRegistering.value) {
      const response = await axios.post(`${API_URL}/register`, {
        username: username.value,
        password: password.value,
        role: role.value
      })
      successMessage.value = response.data.message
      isRegistering.value = false 
      
    } else {
      const response = await axios.post(`${API_URL}/login`, {
        username: username.value,
        password: password.value
      })
      
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('role', response.data.role)
      
      if (response.data.role === 'admin') router.push('/admin')
      else if (response.data.role === 'student') router.push('/student')
      else if (response.data.role === 'company') router.push('/company')
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.message || 'An error occurred.'
  }
}
</script>