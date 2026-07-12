<template>
  <div>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold text-success">Placement Portal V2 | Student Space</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <div class="container">
      
      <div class="row mb-4">
        <div class="col-12">
          <div class="card shadow-sm p-4 bg-dark text-light border-secondary">
            <h5 class="text-info mb-3">Your Professional Resume</h5>
            <div class="d-flex align-items-center gap-3">
              <input 
                type="file" 
                class="form-control form-control-sm bg-secondary text-light border-0 w-50" 
                accept=".pdf" 
                @change="handleFileSelect"
              />
              <button 
                class="btn btn-primary btn-sm px-4" 
                @click="uploadResume" 
                :disabled="!selectedFile || isUploading"
              >
                {{ isUploading ? 'Uploading...' : 'Upload PDF' }}
              </button>
            </div>
            
            <div v-if="currentResumeUrl" class="mt-3 text-muted small">
              Active Resume: 
              <a :href="'http://127.0.0.1:5000' + currentResumeUrl" target="_blank" class="text-warning text-decoration-none fw-bold ms-1">
                View Uploaded Document
              </a>
            </div>
            <div v-else class="mt-3 text-muted small">
              No resume uploaded yet. Please upload a PDF to complete your profile.
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        
        <div class="col-md-7 mb-4">
          <h4 class="mb-3">Available Placement Drives</h4>
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              <div v-if="drives.length === 0" class="p-4 text-muted text-center">
                No active placement drives available right now.
              </div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Role</th>
                    <th>Deadline</th>
                    <th class="text-end">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in drives" :key="drive.id">
                    <td class="align-middle fw-bold text-success">{{ drive.company }}</td>
                    <td class="align-middle">{{ drive.job_title }}</td>
                    <td class="align-middle text-muted">{{ drive.deadline }}</td>
                    <td class="text-end">
                      <button class="btn btn-outline-info btn-sm" @click="applyForDrive(drive.id)">
                        Apply Now
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-md-5 mb-4">
          <h4 class="mb-3">Application Tracker</h4>
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              <div v-if="applications.length === 0" class="p-4 text-muted text-center">
                You haven't applied to any drives yet.
              </div>
              <ul v-else class="list-group list-group-flush">
                <li 
                  v-for="app in applications" 
                  :key="app.application_id"
                  class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center"
                >
                  <div>
                    <div class="fw-bold">{{ app.company_name }}</div>
                    <div class="small text-muted">{{ app.job_title }}</div>
                  </div>
                  <span 
                    class="badge"
                    :class="{
                      'bg-secondary': app.status === 'Applied',
                      'bg-success': app.status === 'Accepted',
                      'bg-danger': app.status === 'Rejected'
                    }"
                  >
                    {{ app.status }}
                  </span>
                </li>
              </ul>
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
const API_URL = 'http://127.0.0.1:5000/api'

// --- State Variables ---
const drives = ref([])
const applications = ref([])
const selectedFile = ref(null)
const isUploading = ref(false)
const currentResumeUrl = ref('') 

// --- API Calls ---

const fetchDrives = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/student/drives`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    drives.value = res.data.data
  } catch (error) {
    console.error("Failed to fetch drives", error)
    if (error.response?.status === 401) handleLogout()
  }
}

const fetchApplications = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/student/my_applications`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    applications.value = res.data
  } catch (error) {
    console.error("Failed to fetch applications", error)
  }
}

const applyForDrive = async (driveId) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/student/apply/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    alert("Application submitted successfully!")
    fetchApplications() // Refresh the tracker instantly
  } catch (error) {
    alert(error.response?.data?.message || "Failed to apply.")
  }
}

// --- Resume Upload Handling ---

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const uploadResume = async () => {
  if (!selectedFile.value) return
  isUploading.value = true
  
  try {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('resume', selectedFile.value)
    
    const response = await axios.post(`${API_URL}/student/upload_resume`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    
    currentResumeUrl.value = response.data.resume_url
    alert("Resume uploaded and attached to profile successfully!")
    selectedFile.value = null // Clear the input
  } catch (error) {
     console.error(error)
     alert(error.response?.data?.message || "Failed to upload resume.")
  } finally {
     isUploading.value = false
  }
}

// --- Lifecycle ---

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

onMounted(() => {
  fetchDrives()
  fetchApplications()
})
</script>