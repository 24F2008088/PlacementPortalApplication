<template>
  <div class="bg-dark text-light min-vh-100 pb-5">
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-dark border-bottom border-secondary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold text-success">Placement Portal V2 | Company Partner</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <div class="container">
      <!-- Tab Navigation -->
      <ul class="nav nav-tabs mb-4 border-secondary">
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'overview' }" @click="activeTab = 'overview'">Dashboard & Inbox</button>
        </li>
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'drives' }" @click="activeTab = 'drives'">Drives</button>
        </li>
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'profile' }" @click="activeTab = 'profile'">Company Profile</button>
        </li>
      </ul>


      <div v-if="activeTab === 'overview'">
        
        <!-- Interactive Analytics Cards -->
        <div class="row mb-4">
          <div class="col-md-4" v-for="(card, key) in analyticsCards" :key="key">
            <div class="card shadow-sm text-center bg-dark text-light border-secondary py-3" @click="openInfoModal(key)" style="cursor: pointer; transition: 0.2s;" onmouseover="this.classList.add('bg-secondary')" onmouseout="this.classList.remove('bg-secondary')">
              <h6 class="text-muted text-uppercase mb-1">{{ card.title }}</h6>
              <h2 class="fw-bold mb-0" :class="card.color">{{ stats[card.statKey] }}</h2>
            </div>
          </div>
        </div>

        <!-- Applicant Inbox -->
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h4 class="mb-0">Applicant Inbox</h4>
        </div>
        
        <div class="card shadow-sm bg-dark text-light border-secondary">
          <div class="card-body p-0">
            <div v-if="applicants.length === 0" class="p-4 text-muted text-center">
              No students have applied to your drives yet.
            </div>
            <table v-else class="table table-dark table-hover mb-0">
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Role Applied For</th>
                  <th>Status</th>
                  <th>Profile</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="app in applicants" :key="app.application_id">
                  <td class="fw-bold text-info align-middle">{{ app.student_name }}</td>
                  <td class="align-middle">{{ app.job_title }}</td>
                  <td class="align-middle">
                    <span class="badge" :class="{'bg-secondary': app.status === 'Applied', 'bg-success': app.status === 'Accepted', 'bg-danger': app.status === 'Rejected'}">
                      {{ app.status }}
                    </span>
                  </td>
                  <td class="align-middle">
                    <button class="btn btn-sm btn-outline-light" @click="openProfileModal(app)">View Profile</button>
                  </td>
                  <td class="align-middle text-end">
                  
                    <div class="btn-group">
                      <button class="btn btn-sm" :class="app.status === 'Accepted' ? 'btn-success' : 'btn-outline-success'" @click="updateStatus(app.application_id, 'accept')">Accept</button>
                      <button class="btn btn-sm" :class="app.status === 'Rejected' ? 'btn-danger' : 'btn-outline-danger'" @click="updateStatus(app.application_id, 'reject')">Reject</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

 
      <div v-if="activeTab === 'drives'" class="row justify-content-center">
        <div class="col-md-10">
          
          
          <div class="card shadow-sm p-4 bg-dark text-light border-secondary mb-5">
            <h5 class="mb-4 text-info">Create a Placement Drive</h5>
            <form @submit.prevent="createDrive">
              <div class="mb-3">
                <label class="form-label text-muted small">Job Title</label>
                <input type="text" class="form-control bg-dark text-light border-secondary" v-model="form.role" required>
              </div>
              <div class="mb-3">
                <label class="form-label text-muted small">Description</label>
                <textarea class="form-control bg-dark text-light border-secondary" v-model="form.description" rows="3"></textarea>
              </div>
              
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label text-muted small">Min CGPA</label>
                  <input type="number" step="0.1" class="form-control bg-dark text-light border-secondary" v-model="form.min_cgpa" required>
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label text-muted small">CTC (LPA)</label>
                  <input type="number" step="0.1" class="form-control bg-dark text-light border-secondary" v-model="form.ctc" required>
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label text-muted small">Application Deadline</label>
                  <input type="date" class="form-control bg-dark text-light border-secondary" v-model="form.deadline" required>
                </div>
              </div>
              
              <button type="submit" class="btn btn-success w-100 mt-2">Post Drive</button>
            </form>
          </div>

        
          <h5 class="mb-3">Manage Active Drives</h5>
          <div class="card shadow-sm bg-dark text-light border-secondary mb-4">
            <div class="card-body p-0">
              <div v-if="myDrives.length === 0" class="p-4 text-muted text-center">
                You haven't created any drives yet.
              </div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Job Title</th>
                    <th>Current Status</th>
                    <th class="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in myDrives" :key="drive.id">
                    <td class="align-middle fw-bold">{{ drive.job_title }}</td>
                    <td class="align-middle">
                      <span class="badge" :class="{'bg-success': drive.status === 'Approved', 'bg-secondary': drive.status === 'Pending', 'bg-danger': drive.status === 'Closed'}">
                        {{ drive.status }}
                      </span>
                    </td>
                    <td class="align-middle text-end">
                      <button 
                        class="btn btn-sm btn-outline-danger" 
                        @click="closeDrive(drive.id)" 
                        :disabled="drive.status === 'Closed'"
                      >
                        {{ drive.status === 'Closed' ? 'Drive Closed' : 'Close Drive' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>

 
      <div v-if="activeTab === 'profile'" class="row justify-content-center">
        <div class="col-md-7">
          <div class="card shadow-sm p-4 bg-dark text-light border-secondary">
            <h5 class="mb-4 text-info">Edit Company Details</h5>
            <form @submit.prevent="updateCompanyProfile">
              <div class="mb-3">
                <label class="form-label text-muted small">Industry (e.g., FinTech, SaaS, AI)</label>
                <input type="text" class="form-control bg-dark text-light border-secondary" v-model="companyForm.industry">
              </div>
              <div class="mb-3">
                <label class="form-label text-muted small">Website URL</label>
                <input type="text" class="form-control bg-dark text-light border-secondary" v-model="companyForm.website" placeholder="https://...">
              </div>
              <div class="mb-4">
                <label class="form-label text-muted small">About the Company</label>
                <textarea class="form-control bg-dark text-light border-secondary" v-model="companyForm.description" rows="4"></textarea>
              </div>
              <button type="submit" class="btn btn-primary w-100">Save Changes</button>
            </form>
          </div>
        </div>
      </div>

    </div>


    <div v-if="activeModal" class="modal-backdrop fade show" style="background-color: rgba(0,0,0,0.7);"></div>
    <div v-if="activeModal" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content bg-dark text-light border-secondary shadow-lg">
          
          <div class="modal-header border-secondary">
            <h5 class="modal-title text-info fw-bold">{{ modalTitle }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeModal"></button>
          </div>
          
          <div class="modal-body p-4">
            <div v-if="activeModal === 'profile'">
              <div class="row mb-3">
                <div class="col-6">
                  <p class="text-muted small mb-1">Branch</p>
                  <p class="fw-bold">{{ selectedStudent.branch }}</p>
                </div>
                <div class="col-6">
                  <p class="text-muted small mb-1">CGPA</p>
                  <p class="fw-bold text-warning">{{ selectedStudent.cgpa }}</p>
                </div>
                <div class="col-12 mt-2">
                  <p class="text-muted small mb-1">Contact Info</p>
                  <p class="fw-bold">{{ selectedStudent.contact_info }}</p>
                </div>
              </div>
              <hr class="border-secondary">
              <a v-if="selectedStudent.resume_file" :href="'http://127.0.0.1:5000' + selectedStudent.resume_file" target="_blank" class="btn btn-outline-info w-100 mt-2">
                <i class="bi bi-file-pdf me-2"></i> View PDF Resume
              </a>
              <p v-else class="text-danger small text-center mt-3">* No resume uploaded.</p>
            </div>
            
            <div v-else>
              <ul class="list-group list-group-flush rounded">
                <li v-for="(item, index) in modalList" :key="index" class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
                  <span class="fw-bold">{{ item.name }}</span>
                  <span class="badge bg-secondary">{{ item.sub }}</span>
                </li>
              </ul>
              <p v-if="modalList.length === 0" class="text-muted text-center py-3 mb-0">No records found.</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const API_URL = 'http://127.0.0.1:5000/api'

// --- State Variables ---
const activeTab = ref('overview')
const activeModal = ref(null)
const selectedStudent = ref(null)
const modalList = ref([])

const stats = ref({ total_drives: 0, total_applicants: 0, total_hired: 0 })
const applicants = ref([])
const myDrives = ref([])

const form = ref({ role: '', description: '', min_cgpa: '', ctc: '', deadline: '' })
const companyForm = ref({ description: '', industry: '', website: '' })

const analyticsCards = {
  drives: { title: 'Active Drives', statKey: 'total_drives', color: 'text-info' },
  applicants: { title: 'Total Applicants', statKey: 'total_applicants', color: 'text-warning' },
  hired: { title: 'Students Hired', statKey: 'total_hired', color: 'text-success' }
}

// --- Computed Properties ---
const modalTitle = computed(() => {
  if (activeModal.value === 'profile') return `${selectedStudent.value.student_name}'s Profile`
  if (activeModal.value === 'drives') return 'My Active Drives'
  if (activeModal.value === 'applicants') return 'All Applicants'
  if (activeModal.value === 'hired') return 'Hired Candidates'
  return ''
})

// --- Modal Controls ---
const openInfoModal = (type) => {
  activeModal.value = type
  if (type === 'drives') modalList.value = myDrives.value.map(d => ({ name: d.job_title, sub: d.status }))
  if (type === 'applicants') modalList.value = applicants.value.map(a => ({ name: a.student_name, sub: a.job_title }))
  if (type === 'hired') modalList.value = applicants.value.filter(a => a.status === 'Accepted').map(a => ({ name: a.student_name, sub: a.job_title }))
}

const openProfileModal = (studentData) => {
  activeModal.value = 'profile'
  selectedStudent.value = studentData
}

const closeModal = () => {
  activeModal.value = null
  selectedStudent.value = null
}

// --- API Calls ---
const fetchAllData = async () => {
  try {
    const token = localStorage.getItem('token')
    const config = { headers: { Authorization: `Bearer ${token}` } }
    
    const [statsRes, appsRes, drivesRes, profileRes] = await Promise.all([
      axios.get(`${API_URL}/company/stats`, config),
      axios.get(`${API_URL}/company/applicants`, config),
      axios.get(`${API_URL}/company/my_drives`, config),
      axios.get(`${API_URL}/company/profile`, config)
    ])
    
    stats.value = statsRes.data
    applicants.value = appsRes.data
    myDrives.value = drivesRes.data
    companyForm.value = profileRes.data
  } catch (error) {
    if (error.response?.status === 401) handleLogout()
    console.error("Failed to fetch dashboard data.", error)
  }
}

const updateStatus = async (applicationId, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/company/${action}_applicant/${applicationId}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchAllData()
  } catch (error) {
    console.error(`Failed to ${action} student.`)
  }
}

const createDrive = async () => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/company/drive`, {
      job_title: form.value.role,
      description: form.value.description,
      eligibility_criteria: form.value.min_cgpa,
      ctc: `${form.value.ctc} LPA`,
      deadline: form.value.deadline 
    }, { headers: { Authorization: `Bearer ${token}` }})
    
    alert("Drive successfully created and pending admin approval!")
    form.value = { role: '', description: '', min_cgpa: '', ctc: '', deadline: '' }
    fetchAllData()
  } catch (error) {
    alert("Failed to create drive.")
  }
}


const closeDrive = async (id) => {
  if(!confirm("Are you sure you want to close this drive? Students will no longer be able to apply.")) return;
  
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/company/close_drive/${id}`, {}, { 
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchAllData() 
  } catch (error) {
    alert("Failed to close drive.")
  }
}

const updateCompanyProfile = async () => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/company/profile`, companyForm.value, { 
      headers: { Authorization: `Bearer ${token}` }
    })
    alert("Company profile saved successfully!")
  } catch (error) {
    alert("Failed to update profile.")
  }
}

onMounted(() => {
  fetchAllData()
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>