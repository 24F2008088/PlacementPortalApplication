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
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-header border-secondary d-flex justify-content-between align-items-center">
              <h5 class="mb-0 text-info">My Professional Profile</h5>
              <button class="btn btn-sm btn-outline-light" @click="isEditing = !isEditing">
                {{ isEditing ? 'Cancel Edit' : 'Edit Profile' }}
              </button>
            </div>
            
            <div class="card-body">
              <div v-if="!isEditing" class="row mb-4">
                <div class="col-md-3"><strong>Full Name:</strong> {{ profile.full_name || 'Not set' }}</div>
                <div class="col-md-3"><strong>Branch:</strong> {{ profile.branch || 'Not set' }}</div>
                <div class="col-md-3"><strong>CGPA:</strong> <span class="text-warning fw-bold">{{ profile.cgpa || 'Not set' }}</span></div>
                <div class="col-md-3"><strong>Contact:</strong> {{ profile.contact_info || 'Not set' }}</div>
              </div>

              <div v-else class="row mb-4 bg-secondary p-3 rounded">
                <div class="col-md-3 mb-2">
                  <label class="form-label small">Full Name</label>
                  <input type="text" v-model="editForm.full_name" class="form-control form-control-sm bg-dark text-light border-0">
                </div>
                <div class="col-md-3 mb-2">
                  <label class="form-label small">Branch</label>
                  <input type="text" v-model="editForm.branch" class="form-control form-control-sm bg-dark text-light border-0">
                </div>
                <div class="col-md-3 mb-2">
                  <label class="form-label small">Current CGPA</label>
                  <input type="number" step="0.01" v-model="editForm.cgpa" class="form-control form-control-sm bg-dark text-light border-0">
                </div>
                <div class="col-md-3 mb-2">
                  <label class="form-label small">Contact Info</label>
                  <input type="text" v-model="editForm.contact_info" class="form-control form-control-sm bg-dark text-light border-0">
                </div>
                <div class="col-12 mt-2 text-end">
                  <button class="btn btn-success btn-sm px-4" @click="saveProfile" :disabled="isSaving">
                    {{ isSaving ? 'Saving...' : 'Save Profile' }}
                  </button>
                </div>
              </div>

              <hr class="border-secondary">

              <h6 class="text-light mb-3">Resume Document</h6>
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
              <div v-else class="mt-3 text-danger small">
                * No resume uploaded. A PDF is required for most applications.
              </div>
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
                    <th>Req. CGPA</th>
                    <th>Deadline</th> <!-- NEW COLUMN -->
                    <th class="text-end">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in drives" :key="drive.id">
                    <td class="align-middle fw-bold text-success">{{ drive.company }}</td>
                    <td class="align-middle">{{ drive.job_title }}</td>
                    <td class="align-middle text-warning">{{ drive.eligibility_criteria || 'None' }}</td>
                    <td class="align-middle" :class="isDeadlinePassed(drive.deadline) ? 'text-danger' : 'text-light'">
                      {{ drive.deadline || 'N/A' }}
                    </td>
                    <td class="text-end align-middle">
                      
                      <!-- 1. Check if already applied -->
                      <button 
                        v-if="hasApplied(drive.id)" 
                        class="btn btn-sm btn-success text-light" 
                        disabled
                      >
                        <i class="bi bi-check-circle me-1"></i> Already Applied
                      </button>

                      <!-- 2. Check if deadline has passed -->
                      <button 
                        v-else-if="isDeadlinePassed(drive.deadline)" 
                        class="btn btn-sm btn-danger text-light" 
                        disabled
                      >
                        <i class="bi bi-x-circle me-1"></i> Deadline Passed
                      </button>

                      <!-- 3. Check if eligible -->
                      <button 
                        v-else-if="!isEligible(drive.eligibility_criteria)" 
                        class="btn btn-sm btn-outline-secondary" 
                        disabled 
                        title="Your CGPA does not meet the requirement"
                      >
                        Ineligible
                      </button>

                      <!-- 4. Default Apply Button -->
                      <button 
                        v-else 
                        class="btn btn-sm btn-outline-info" 
                        @click="applyForDrive(drive.id)"
                      >
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
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h4 class="mb-0">Application Tracker</h4>
            <!-- Export History Button -->
            <button 
              class="btn btn-outline-warning btn-sm" 
              @click="exportHistory"
              :disabled="isExporting"
            >
              {{ isExporting ? 'Exporting...' : 'Export History (CSV)' }}
            </button>
          </div>
          
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
const isExporting = ref(false)

// Profile State
const profile = ref({ full_name: '', branch: '', cgpa: '', contact_info: '' })
const editForm = ref({ full_name: '', branch: '', cgpa: '', contact_info: '' })
const isEditing = ref(false)
const isSaving = ref(false)

// Resume State
const selectedFile = ref(null)
const isUploading = ref(false)
const currentResumeUrl = ref('') 

// --- Core API Calls ---

const fetchProfile = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/student/profile`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    profile.value = res.data
    editForm.value = { ...res.data }
    currentResumeUrl.value = res.data.resume_file || ''
  } catch (error) {
    console.error("Failed to fetch profile", error)
  }
}

const saveProfile = async () => {
  isSaving.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/student/profile`, editForm.value, {
      headers: { Authorization: `Bearer ${token}` }
    })
    profile.value = { ...editForm.value }
    isEditing.value = false
  } catch (error) {
    alert(error.response?.data?.message || "Failed to save profile.")
  } finally {
    isSaving.value = false
  }
}

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

// --- Status & Guardrail Logic ---

// NEW: Deadline check function
const isDeadlinePassed = (deadline) => {
  if (!deadline) return false
  
  // Set today's date to midnight so it compares exactly to the day
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const driveDeadline = new Date(deadline)
  return driveDeadline < today
}

const isEligible = (criteria) => {
  if (!criteria) return true
  if (!profile.value.cgpa) return false 

  const requiredCgpa = parseFloat(criteria)
  const studentCgpa = parseFloat(profile.value.cgpa)

  if (isNaN(requiredCgpa)) return true 
  
  return studentCgpa >= requiredCgpa
}

const hasApplied = (driveId) => {
  return applications.value.some(app => app.drive_id === driveId)
}

const applyForDrive = async (driveId) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/student/apply/${driveId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    alert("Application submitted successfully!")
    fetchApplications()
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
    selectedFile.value = null
  } catch (error) {
     console.error(error)
     alert(error.response?.data?.message || "Failed to upload resume.")
  } finally {
     isUploading.value = false
  }
}

// --- CSV Export Handling (Celery Task) ---

const exportHistory = async () => {
  isExporting.value = true
  try {
    const token = localStorage.getItem('token')
    
    const startResponse = await axios.post(`${API_URL}/student/export`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    const taskId = startResponse.data.task_id
    
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await axios.get(`${API_URL}/student/export_status/${taskId}`)
        
        if (statusResponse.data.status === 'Ready') {
          clearInterval(pollInterval)
          isExporting.value = false
          
          const link = document.createElement('a')
          link.href = statusResponse.data.download_url
          link.setAttribute('download', '') 
          document.body.appendChild(link)
          link.click()
          link.remove()
        } 
      } catch (pollError) {
        clearInterval(pollInterval)
        isExporting.value = false
        alert("The background export task failed.")
      }
    }, 2000)
    
  } catch (error) {
    console.error(error)
    isExporting.value = false
    alert("Failed to connect to export service.")
  }
}

// --- Lifecycle ---

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

onMounted(() => {
  fetchProfile()
  fetchDrives()
  fetchApplications()
})
</script>