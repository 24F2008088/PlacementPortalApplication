<template>
  <div class="bg-dark text-light min-vh-100 pb-5">
    <nav class="navbar navbar-expand-lg bg-dark border-bottom border-secondary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold text-primary">Placement Portal  |  Admin Command Center</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <div class="container">
      
      <ul class="nav nav-tabs mb-4 border-secondary">
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'overview' }" @click="activeTab = 'overview'">Dashboard & Analytics</button>
        </li>
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'management' }" @click="activeTab = 'management'">Management</button>
        </li>
      </ul>

      <div v-if="activeTab === 'overview'">
        
        <div class="row mb-4">
          <div class="col-md-3">
            <div class="card shadow-sm text-center bg-dark text-light border-secondary py-3">
              <h6 class="text-muted text-uppercase mb-1 small">Total Students</h6>
              <h3 class="fw-bold text-success mb-0">{{ rawStats.total_students }}</h3>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card shadow-sm text-center bg-dark text-light border-secondary py-3">
              <h6 class="text-muted text-uppercase mb-1 small">Total Companies</h6>
              <h3 class="fw-bold text-warning mb-0">{{ rawStats.total_companies }}</h3>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card shadow-sm text-center bg-dark text-light border-secondary py-3">
              <h6 class="text-muted text-uppercase mb-1 small">Active Drives</h6>
              <h3 class="fw-bold text-info mb-0">{{ rawStats.total_drives }}</h3>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card shadow-sm text-center bg-dark text-light border-secondary py-3">
              <h6 class="text-muted text-uppercase mb-1 small">Total Applications</h6>
              <h3 class="fw-bold text-primary mb-0">{{ rawStats.total_applications }}</h3>
            </div>
          </div>
        </div>

        <div class="row mb-5">
          <div class="col-12">
            <div class="card shadow-sm bg-dark border-secondary">
              <div class="card-header border-secondary text-light fw-bold">Platform Activity Chart</div>
              <div class="card-body" style="height: 350px;">
                <Bar v-if="isChartLoaded" id="my-chart-id" :options="chartOptions" :data="chartData" />
                <div v-else class="text-center text-muted mt-5">Loading analytics...</div>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-4">
            <div class="card shadow-sm bg-dark text-light border-secondary">
              <div class="card-header border-secondary fw-bold text-warning">Pending Company Approvals</div>
              <div class="card-body p-0">
                <div v-if="pendingCompanies.length === 0" class="p-4 text-muted text-center">No pending companies.</div>
                <table v-else class="table table-dark table-hover mb-0">
                  <tbody>
                    <tr v-for="company in pendingCompanies" :key="company.id">
                      <td class="align-middle fw-bold">{{ company.username }}</td>
                      <td class="text-end">
                        <button class="btn btn-success btn-sm me-2" @click="handleCompany(company.id, 'approve')">Approve</button>
                        <button class="btn btn-danger btn-sm" @click="handleCompany(company.id, 'reject')">Reject</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="col-md-6 mb-4">
            <div class="card shadow-sm bg-dark text-light border-secondary">
              <div class="card-header border-secondary fw-bold text-info">Pending Drive Approvals</div>
              <div class="card-body p-0">
                <div v-if="pendingDrives.length === 0" class="p-4 text-muted text-center">No pending drives.</div>
                <table v-else class="table table-dark table-hover mb-0">
                  <tbody>
                    <tr v-for="drive in pendingDrives" :key="drive.id">
                      <td class="align-middle fw-bold">{{ drive.job_title }}</td>
                      <td class="text-end">
                        <button class="btn btn-success btn-sm me-2" @click="handleDrive(drive.id, 'approve')">Approve</button>
                        <button class="btn btn-danger btn-sm" @click="handleDrive(drive.id, 'reject')">Reject</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'management'">
        
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div class="btn-group shadow-sm">
            <button class="btn" :class="subTab === 'users' ? 'btn-primary fw-bold' : 'btn-outline-primary'" @click="subTab = 'users'">Users</button>
            <button class="btn" :class="subTab === 'drives' ? 'btn-info fw-bold' : 'btn-outline-info'" @click="subTab = 'drives'">All Drives</button>
            <button class="btn" :class="subTab === 'apps' ? 'btn-warning fw-bold' : 'btn-outline-warning'" @click="subTab = 'apps'">All Applications</button>
          </div>
          
          <button class="btn btn-sm btn-outline-light" @click="refreshManagementData">
            <i class="bi bi-arrow-clockwise me-1"></i> Refresh Data
          </button>
        </div>

        <div v-if="subTab === 'users'">
          <div class="d-flex justify-content-end mb-3">
            <input type="text" class="form-control form-control-sm bg-dark text-light border-secondary" v-model="searchQuery" placeholder="Search by username..." style="width: 250px;">
          </div>

          <h5 class="mb-3 text-info">Student Accounts</h5>
          <div class="card shadow-sm bg-dark text-light border-secondary mb-5">
            <div class="card-body p-0">
              <div v-if="studentsList.length === 0" class="p-4 text-muted text-center">{{ searchQuery ? 'No students match your search.' : 'No students registered yet.' }}</div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead><tr><th>Username</th><th>Approval Status</th><th class="text-end">Account Action</th></tr></thead>
                <tbody>
                  <tr v-for="user in studentsList" :key="user.id">
                    <td class="align-middle fw-bold" :class="user.is_blacklisted ? 'text-decoration-line-through text-muted' : 'text-light'">{{ user.username }}</td>
                    <td class="align-middle">
                      <span v-if="user.is_approved" class="badge bg-success">Approved</span>
                      <span v-else class="badge bg-warning text-dark">Pending</span>
                    </td>
                    <td class="text-end align-middle">
                      <button class="btn btn-sm" :class="user.is_blacklisted ? 'btn-outline-success' : 'btn-danger'" @click="toggleBlacklist(user.id)">{{ user.is_blacklisted ? 'Restore Access' : 'Blacklist' }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <h5 class="mb-3 text-warning">Company Accounts</h5>
          <div class="card shadow-sm bg-dark text-light border-secondary mb-4">
            <div class="card-body p-0">
              <div v-if="companiesList.length === 0" class="p-4 text-muted text-center">{{ searchQuery ? 'No companies match your search.' : 'No companies registered yet.' }}</div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead><tr><th>Company Name</th><th>Approval Status</th><th class="text-end">Account Action</th></tr></thead>
                <tbody>
                  <tr v-for="user in companiesList" :key="user.id">
                    <td class="align-middle fw-bold" :class="user.is_blacklisted ? 'text-decoration-line-through text-muted' : 'text-light'">{{ user.username }}</td>
                    <td class="align-middle">
                      <span v-if="user.is_approved" class="badge bg-success">Approved</span>
                      <span v-else class="badge bg-warning text-dark">Pending</span>
                    </td>
                    <td class="text-end align-middle">
                      <button class="btn btn-sm" :class="user.is_blacklisted ? 'btn-outline-success' : 'btn-danger'" @click="toggleBlacklist(user.id)">{{ user.is_blacklisted ? 'Restore Access' : 'Blacklist' }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-if="subTab === 'drives'">
          <div class="card shadow-sm bg-dark text-light border-secondary mb-4">
            <div class="card-header border-secondary fw-bold text-info">Platform Drive Database</div>
            <div class="card-body p-0">
              <div v-if="allDrives.length === 0" class="p-4 text-muted text-center">No placement drives exist on the platform.</div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Job Title</th>
                    <th>CTC</th>
                    <th>Deadline</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in allDrives" :key="drive.id">
                    <td class="align-middle text-warning fw-bold">{{ drive.company }}</td>
                    <td class="align-middle">{{ drive.job_title }}</td>
                    <td class="align-middle">{{ drive.ctc || 'N/A' }}</td>
                    <td class="align-middle">{{ drive.deadline || 'N/A' }}</td>
                    <td class="align-middle">
                      <span class="badge" :class="{'bg-success': drive.status === 'Approved', 'bg-secondary': drive.status === 'Pending'}">{{ drive.status }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-if="subTab === 'apps'">
          <div class="card shadow-sm bg-dark text-light border-secondary mb-4">
            <div class="card-header border-secondary fw-bold text-warning">Platform Application Database</div>
            <div class="card-body p-0">
              <div v-if="allApplications.length === 0" class="p-4 text-muted text-center">No students have applied to any drives yet.</div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Student Username</th>
                    <th>Target Company</th>
                    <th>Job Title</th>
                    <th>Current Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in allApplications" :key="app.id">
                    <td class="align-middle text-info fw-bold">{{ app.student_name }}</td>
                    <td class="align-middle text-warning">{{ app.company_name }}</td>
                    <td class="align-middle">{{ app.job_title }}</td>
                    <td class="align-middle">
                      <span class="badge" :class="{'bg-secondary': app.status === 'Applied', 'bg-success': app.status === 'Accepted', 'bg-danger': app.status === 'Rejected'}">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const router = useRouter()
const API_URL = 'http://127.0.0.1:5000/api'

// --- State Variables ---
const activeTab = ref('overview')
const subTab = ref('users') 

const pendingCompanies = ref([])
const pendingDrives = ref([])

// Management Data
const usersList = ref([])
const allDrives = ref([])
const allApplications = ref([])
const searchQuery = ref('') 

// Chart Data
const isChartLoaded = ref(false)
const rawStats = ref({ total_students: 0, total_companies: 0, total_drives: 0, total_applications: 0 })

// --- Computed Properties ---
const studentsList = computed(() => {
  let filtered = usersList.value.filter(user => user.role === 'student')
  if (searchQuery.value) {
    filtered = filtered.filter(user => user.username.toLowerCase().includes(searchQuery.value.toLowerCase()))
  }
  return filtered
})

const companiesList = computed(() => {
  let filtered = usersList.value.filter(user => user.role === 'company')
  if (searchQuery.value) {
    filtered = filtered.filter(user => user.username.toLowerCase().includes(searchQuery.value.toLowerCase()))
  }
  return filtered
})

// --- Chart Configuration ---
const chartData = ref({
  labels: ['Students', 'Companies', 'Drives', 'Applications'],
  datasets: [{
    label: 'Total Count',
    backgroundColor: ['#42b883', '#ffc107', '#0dcaf0', '#0d6efd'],
    data: [0, 0, 0, 0] 
  }]
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { beginAtZero: true, ticks: { stepSize: 1, color: '#adb5bd' }, grid: { color: '#495057' } },
    x: { ticks: { color: '#adb5bd' }, grid: { display: false } }
  }
})

// --- API Calls ---

const fetchStats = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } })
    
    rawStats.value = res.data.data
    chartData.value.datasets[0].data = [
      rawStats.value.total_students, 
      rawStats.value.total_companies, 
      rawStats.value.total_drives, 
      rawStats.value.total_applications
    ]
    isChartLoaded.value = true
  } catch (error) {
    if (error.response?.status === 401) handleLogout()
  }
}

const fetchPending = async () => {
  try {
    const token = localStorage.getItem('token')
    const config = { headers: { Authorization: `Bearer ${token}` } }
    const [compRes, driveRes] = await Promise.all([
      axios.get(`${API_URL}/admin/pending_companies`, config),
      axios.get(`${API_URL}/admin/pending_drives`, config)
    ])
    pendingCompanies.value = compRes.data
    pendingDrives.value = driveRes.data
  } catch (error) {
    console.error("Failed to fetch pending requests", error)
  }
}

// Master function to fetch all management databases
const refreshManagementData = async () => {
  try {
    const token = localStorage.getItem('token')
    const config = { headers: { Authorization: `Bearer ${token}` } }
    
    const [usersRes, drivesRes, appsRes] = await Promise.all([
      axios.get(`${API_URL}/admin/users`, config),
      axios.get(`${API_URL}/admin/all_drives`, config),
      axios.get(`${API_URL}/admin/all_applications`, config)
    ])
    
    usersList.value = usersRes.data
    allDrives.value = drivesRes.data
    allApplications.value = appsRes.data
  } catch (error) {
    console.error("Failed to fetch management databases.", error)
  }
}

// Action Handlers
const handleCompany = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_company/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    fetchPending(); fetchStats(); refreshManagementData();
  } catch (error) {
    alert(`Failed to ${action} company.`)
  }
}

const handleDrive = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_drive/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    fetchPending(); fetchStats(); refreshManagementData();
  } catch (error) {
    alert(`Failed to ${action} drive.`)
  }
}

const toggleBlacklist = async (id) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/toggle_blacklist/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    refreshManagementData() 
  } catch (error) {
    alert("Failed to change user status.")
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

// Fetch all data on load
onMounted(() => {
  fetchStats()
  fetchPending()
  refreshManagementData()
})
</script>