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
      
      <!-- Alerts (Kept these so they know if an application succeeded) -->
      <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

      <div class="row">
        
        <!-- Left Column: Available Job Board -->
        <div class="col-md-6 mb-4">
          <h4 class="mb-3">Available Placement Drives</h4>
          
          <div v-if="drives.length === 0" class="alert alert-info border-info bg-dark text-info">
            No placement drives available right now.
          </div>

          <div v-for="drive in drives" :key="drive.id" class="card shadow-sm mb-3 bg-dark text-light border-secondary">
            <div class="card-body">
              <h5 class="card-title text-info">{{ drive.company_name || 'Company' }}</h5>
              <h6 class="card-subtitle mb-3 text-secondary">{{ drive.role || drive.job_title }}</h6>
              <p class="card-text text-muted mb-2">{{ drive.description }}</p>
              
              <div class="mb-3">
                <span class="badge bg-primary me-2">{{ drive.eligibility || 'Requirements TBD' }}</span>
              </div>
              
              <button class="btn btn-outline-info btn-sm" @click="applyForDrive(drive.id)">
                Apply Now
              </button>
            </div>
          </div>
        </div>

        <!-- Right Column: My Application Tracker -->
        <div class="col-md-6">
          <h4 class="mb-3">My Application Tracker</h4>
          
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              
              <div v-if="myApplications.length === 0" class="p-4 text-muted text-center">
                You haven't applied to any drives yet.
              </div>
              
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in myApplications" :key="app.application_id">
                    <td class="fw-bold">{{ app.company_name }}</td>
                    <td>{{ app.job_title }}</td>
                    <td>
                      <!-- Dynamic badges based on what the Company chose! -->
                      <span class="badge" 
                            :class="{
                              'bg-secondary': app.status === 'Applied',
                              'bg-success': app.status === 'Accepted',
                              'bg-danger': app.status === 'Rejected'
                            }">
                        {{ app.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              
            </div>
          </div>
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
const myApplications = ref([]) 
const errorMessage = ref('')
const successMessage = ref('')
const API_URL = 'http://127.0.0.1:5000/api'

// 1. Fetch available drives
const fetchDrives = async () => {
  try {
    const token = localStorage.getItem('token') 
    const response = await axios.get(`${API_URL}/student/drives`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    drives.value = response.data.data || response.data 
  } catch (error) {
    console.error("Failed to load placement drives.")
    if (error.response?.status === 401) handleLogout()
  }
}

// 2. Fetch the student's personal applications
const fetchMyApplications = async () => {
  try {
    const token = localStorage.getItem('token') 
    const response = await axios.get(`${API_URL}/student/my_applications`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    myApplications.value = response.data 
  } catch (error) {
    console.error("Failed to load application history.")
  }
}

// 3. Apply for a drive
const applyForDrive = async (driveId) => {
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post(`${API_URL}/student/apply/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    successMessage.value = response.data.message
    
    // Auto-clear success message after 3 seconds
    setTimeout(() => successMessage.value = '', 3000)
    
    // Refresh the application tracker instantly!
    fetchMyApplications()
    
  } catch (error) {
    errorMessage.value = error.response?.data?.message || 'Failed to apply for the drive.'
    setTimeout(() => errorMessage.value = '', 3000)
  }
}

onMounted(() => {
  fetchDrives()
  fetchMyApplications()
})

const handleLogout = () => {
  localStorage.removeItem('token') 
  localStorage.removeItem('role')
  router.push('/login') 
}
</script>