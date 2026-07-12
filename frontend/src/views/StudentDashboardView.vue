<template>
  <div>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold">Placement Portal V2 | Student</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="container">
      <h2 class="mb-4">Available Placement Drives</h2>
      
      <!-- Alerts -->
      <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

      <div v-if="drives.length === 0" class="alert alert-info border-info bg-dark text-info">
        No placement drives available right now.
      </div>

      <!-- Drive Cards -->
      <div v-for="drive in drives" :key="drive.id" class="card shadow-sm mb-3 bg-dark text-light border-secondary">
        <div class="card-body">
          <h5 class="card-title text-info">{{ drive.company_name || 'Company' }}</h5>
          <h6 class="card-subtitle mb-3 text-secondary">{{ drive.role || drive.job_title }}</h6>
          <p class="card-text text-muted mb-2">{{ drive.description }}</p>
          
          <div class="mb-3">
            <!-- Cleaned up the badge UI here! -->
            <span class="badge bg-primary me-2">{{ drive.eligibility || 'Requirements TBD' }}</span>
          </div>
          
          <!-- Wired up the Apply button -->
          <button class="btn btn-outline-info btn-sm" @click="applyForDrive(drive.id)">
            Apply Now
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const drives = ref([]) 
const errorMessage = ref('')
const successMessage = ref('')
const API_URL = 'http://127.0.0.1:5000/api'

const fetchDrives = async () => {
  try {
    const token = localStorage.getItem('token') 
    const response = await axios.get(`${API_URL}/student/drives`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    drives.value = response.data.data || response.data 
  } catch (error) {
    errorMessage.value = "Failed to load placement drives."
    if (error.response?.status === 401) handleLogout()
  }
}

// NEW: Function to handle applying for a job
const applyForDrive = async (driveId) => {
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    const token = localStorage.getItem('token')
    
    const response = await axios.post(`${API_URL}/student/apply/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    successMessage.value = response.data.message
    
  } catch (error) {
    errorMessage.value = error.response?.data?.message || 'Failed to apply for the drive.'
  }
}

onMounted(() => {
  fetchDrives()
})

const handleLogout = () => {
  localStorage.removeItem('token') 
  localStorage.removeItem('role')
  router.push('/login') 
}
</script>