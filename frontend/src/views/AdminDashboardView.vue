<template>
  <div>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold">Placement Portal V2 | Admin</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="container">
      <h2 class="mb-4">Admin Dashboard</h2>
      
      <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

      <!-- 1. Pending Company Approvals -->
      <div class="card bg-dark text-light border-secondary mb-4 shadow-sm">
        <div class="card-header border-secondary text-warning fw-bold">
          Pending Company Approvals
        </div>
        <div class="card-body">
          <div v-if="pendingCompanies.length === 0" class="text-muted">
            No pending company approvals at this time.
          </div>
          
          <ul class="list-group list-group-flush">
            <li v-for="company in pendingCompanies" :key="company.id" class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
              <div>
                <strong>{{ company.username }}</strong>
                <span class="badge bg-secondary ms-2">Awaiting Approval</span>
              </div>
              <div class="btn-group">
                <button class="btn btn-success btn-sm" @click="approveCompany(company.id)">Approve</button>
                <button class="btn btn-danger btn-sm" @click="rejectCompany(company.id)">Reject</button>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- 2. NEW: Pending Drive Approvals -->
      <div class="card bg-dark text-light border-secondary mb-4 shadow-sm">
        <div class="card-header border-secondary text-info fw-bold">
          Pending Placement Drives
        </div>
        <div class="card-body">
          <div v-if="pendingDrives.length === 0" class="text-muted">
            No pending placement drives at this time.
          </div>
          
          <ul class="list-group list-group-flush">
            <li v-for="drive in pendingDrives" :key="drive.id" class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
              <div>
                <strong>{{ drive.job_title }}</strong>
                <div class="text-muted small">{{ drive.description }}</div>
              </div>
              <div class="btn-group">
                <button class="btn btn-success btn-sm" @click="approveDrive(drive.id)">Approve</button>
                <button class="btn btn-danger btn-sm" @click="rejectDrive(drive.id)">Reject</button>
              </div>
            </li>
          </ul>
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
const API_URL = 'http://127.0.0.1:5000/api'

const pendingCompanies = ref([])
const pendingDrives = ref([])
const errorMessage = ref('')
const successMessage = ref('')

// --- Company Functions ---
const fetchPendingCompanies = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/admin/pending_companies`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    pendingCompanies.value = response.data
  } catch (error) {
    errorMessage.value = "Failed to load pending companies."
    if (error.response?.status === 401) handleLogout()
  }
}

const approveCompany = async (companyId) => {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/approve_company/${companyId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    successMessage.value = "Company approved successfully!"
    fetchPendingCompanies()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || "Failed to approve company."
  }
}

const rejectCompany = async (companyId) => {
  if (!window.confirm("Are you sure you want to reject and delete this company?")) return;
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/reject_company/${companyId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    successMessage.value = "Company rejected and removed."
    fetchPendingCompanies()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || "Failed to reject company."
  }
}

// --- Drive Functions ---
const fetchPendingDrives = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/admin/pending_drives`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    pendingDrives.value = response.data
  } catch (error) {
    errorMessage.value = "Failed to load pending drives."
  }
}

const approveDrive = async (driveId) => {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/approve_drive/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    successMessage.value = "Drive approved successfully!"
    fetchPendingDrives() // Refresh the list
  } catch (error) {
    errorMessage.value = error.response?.data?.message || "Failed to approve drive."
  }
}

const rejectDrive = async (driveId) => {
  if (!window.confirm("Are you sure you want to reject and delete this drive?")) return;
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/reject_drive/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    successMessage.value = "Drive rejected and removed."
    fetchPendingDrives() // Refresh the list
  } catch (error) {
    errorMessage.value = error.response?.data?.message || "Failed to reject drive."
  }
}

// Run both fetch functions when the page loads
onMounted(() => {
  fetchPendingCompanies()
  fetchPendingDrives()
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>