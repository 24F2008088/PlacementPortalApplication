<template>
  <div>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold">Placement Portal V2 | Company Partner</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="container">
      
  

      <div class="row">
        <!-- Left Column: Create Drive Form -->
        <div class="col-md-5 mb-4">
          <h4 class="mb-3">Create New Drive</h4>
          <div class="card shadow-sm p-4 bg-dark text-light border-secondary">
            <form @submit.prevent="createDrive">
              <div class="mb-3">
                <label class="form-label">Role Offered (Job Title)</label>
                <input type="text" class="form-control" v-model="form.role" required>
              </div>
              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control" v-model="form.description" rows="3"></textarea>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Minimum CGPA</label>
                  <input type="number" step="0.1" class="form-control" v-model="form.min_cgpa" required>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">CTC (in LPA)</label>
                  <input type="number" class="form-control" v-model="form.ctc" required>
                </div>
              </div>
              <button type="submit" class="btn btn-success w-100 mt-2">Post Drive</button>
            </form>
          </div>
        </div>

        <!-- Right Column: Applicant Inbox -->
        <div class="col-md-7">
          <h4 class="mb-3">Applicant Inbox</h4>
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              
              <div v-if="applicants.length === 0" class="p-4 text-muted text-center">
                No students have applied to your drives yet.
              </div>
              
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Role Applied For</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in applicants" :key="app.application_id">
                    <td class="fw-bold text-info align-middle">{{ app.student_name }}</td>
                    <td class="align-middle">{{ app.job_title }}</td>
                    <td class="align-middle">
                      <!-- Badge changes color based on status -->
                      <span class="badge" 
                            :class="{
                              'bg-secondary': app.status === 'Applied',
                              'bg-success': app.status === 'Accepted',
                              'bg-danger': app.status === 'Rejected'
                            }">
                        {{ app.status }}
                      </span>
                    </td>
                    <td class="align-middle">
                      <!-- Only show buttons if a decision hasn't been made yet -->
                      <div v-if="app.status === 'Applied'" class="btn-group">
                        <button class="btn btn-outline-success btn-sm" @click="updateStatus(app.application_id, 'accept')">Accept</button>
                        <button class="btn btn-outline-danger btn-sm" @click="updateStatus(app.application_id, 'reject')">Reject</button>
                      </div>
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
const API_URL = 'http://127.0.0.1:5000/api'

const form = ref({ role: '', description: '', min_cgpa: '', ctc: '' })
const applicants = ref([])


// 1. Post a new drive
const createDrive = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const token = localStorage.getItem('token')
    const formattedData = {
      job_title: form.value.role,
      description: form.value.description,
      eligibility: `Min CGPA: ${form.value.min_cgpa} | CTC: ${form.value.ctc} LPA`,
      deadline: '2026-12-31' 
    }

    await axios.post(`${API_URL}/company/drive`, formattedData, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    successMessage.value = "Drive successfully created and pending admin approval!"
    form.value = { role: '', description: '', min_cgpa: '', ctc: '' }
    
  } catch (error) {
    errorMessage.value = error.response?.data?.message || 'Failed to create drive.'
    if (error.response?.status === 401) handleLogout()
  }
}

// 2. Fetch the students who applied
const fetchApplicants = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/company/applicants`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    applicants.value = response.data
  } catch (error) {
    console.error("Error fetching applicants:", error)
  }
}

// 3. NEW: Accept or Reject an applicant
const updateStatus = async (applicationId, action) => {
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    const token = localStorage.getItem('token')
    
    // Choose the correct route based on which button was clicked
    const route = action === 'accept' ? 'accept_applicant' : 'reject_applicant'
    
    const response = await axios.post(`${API_URL}/company/${route}/${applicationId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    successMessage.value = response.data.message
    fetchApplicants() // Refresh the table to update the UI instantly
    
  } catch (error) {
    errorMessage.value = error.response?.data?.message || `Failed to ${action} student.`
  }
}

onMounted(() => {
  fetchApplicants()
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>