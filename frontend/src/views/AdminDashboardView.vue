<template>
  <div class="bg-dark text-light min-vh-100 pb-5">
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-dark border-bottom border-secondary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold text-primary">Placement Portal V2 | Admin Command Center</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <div class="container">
      
      <!-- Tabbed Navigation -->
      <ul class="nav nav-tabs mb-4 border-secondary">
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'overview' }" @click="activeTab = 'overview'">Dashboard & Analytics</button>
        </li>
        <li class="nav-item">
          <button class="nav-link text-light border-secondary" :class="{ 'active bg-secondary fw-bold': activeTab === 'users' }" @click="activeTab = 'users'">User Management</button>
        </li>
      </ul>

      <!-- ========================================== -->
      <!-- TAB 1: OVERVIEW & ANALYTICS                -->
      <!-- ========================================== -->
      <div v-if="activeTab === 'overview'">
        
        <!-- 1. "At-a-Glance" Metric Cards -->
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

        <!-- 2. The Analytics Chart -->
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

        <!-- 3. Pending Approvals -->
        <div class="row">
          <!-- Pending Companies -->
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

          <!-- Pending Drives -->
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

      <!-- ========================================== -->
      <!-- TAB 2: USER MANAGEMENT & BLACKLISTING      -->
      <!-- ========================================== -->
      <div v-if="activeTab === 'users'">
        
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h4 class="mb-0 text-light">Platform Users</h4>
          
          <!-- SEARCH & REFRESH CONTROLS -->
          <div class="d-flex gap-2">
            <input 
              type="text" 
              class="form-control form-control-sm bg-dark text-light border-secondary" 
              v-model="searchQuery" 
              placeholder="Search by username..."
              style="width: 250px;"
            >
            <button class="btn btn-sm btn-outline-light text-nowrap" @click="fetchUsers">Refresh Lists</button>
          </div>
        </div>

        <!-- Student Database Table -->
        <h5 class="mt-4 mb-3 text-info">Student Accounts</h5>
        <div class="card shadow-sm bg-dark text-light border-secondary mb-5">
          <div class="card-body p-0">
            <div v-if="studentsList.length === 0" class="p-4 text-muted text-center">
              {{ searchQuery ? 'No students match your search.' : 'No students registered yet.' }}
            </div>
            <table v-else class="table table-dark table-hover mb-0">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Approval Status</th>
                  <th class="text-end">Account Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in studentsList" :key="user.id">
                  <td class="align-middle fw-bold" :class="user.is_blacklisted ? 'text-decoration-line-through text-muted' : 'text-light'">
                    {{ user.username }}
                  </td>
                  <td class="align-middle">
                    <span v-if="user.is_approved" class="badge bg-success">Approved</span>
                    <span v-else class="badge bg-warning text-dark">Pending</span>
                  </td>
                  <td class="text-end align-middle">
                    <button 
                      class="btn btn-sm" 
                      :class="user.is_blacklisted ? 'btn-outline-success' : 'btn-danger'"
                      @click="toggleBlacklist(user.id)"
                    >
                      {{ user.is_blacklisted ? 'Restore Access' : 'Blacklist Student' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Company Database Table -->
        <h5 class="mb-3 text-warning">Company Accounts</h5>
        <div class="card shadow-sm bg-dark text-light border-secondary mb-4">
          <div class="card-body p-0">
            <div v-if="companiesList.length === 0" class="p-4 text-muted text-center">
              {{ searchQuery ? 'No companies match your search.' : 'No companies registered yet.' }}
            </div>
            <table v-else class="table table-dark table-hover mb-0">
              <thead>
                <tr>
                  <th>Company Name</th>
                  <th>Approval Status</th>
                  <th class="text-end">Account Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in companiesList" :key="user.id">
                  <td class="align-middle fw-bold" :class="user.is_blacklisted ? 'text-decoration-line-through text-muted' : 'text-light'">
                    {{ user.username }}
                  </td>
                  <td class="align-middle">
                    <span v-if="user.is_approved" class="badge bg-success">Approved</span>
                    <span v-else class="badge bg-warning text-dark">Pending</span>
                  </td>
                  <td class="text-end align-middle">
                    <button 
                      class="btn btn-sm" 
                      :class="user.is_blacklisted ? 'btn-outline-success' : 'btn-danger'"
                      @click="toggleBlacklist(user.id)"
                    >
                      {{ user.is_blacklisted ? 'Restore Access' : 'Blacklist Company' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
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
const pendingCompanies = ref([])
const pendingDrives = ref([])
const usersList = ref([])
const searchQuery = ref('') // NEW: Tracks the search input
const isChartLoaded = ref(false)
const rawStats = ref({ total_students: 0, total_companies: 0, total_drives: 0, total_applications: 0 })

// --- Computed Properties (Now with Search Logic!) ---
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

const fetchUsers = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
    usersList.value = res.data
  } catch (error) {
    console.error("Failed to fetch user list", error)
  }
}

const handleCompany = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_company/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    fetchPending(); fetchStats(); fetchUsers();
  } catch (error) {
    alert(`Failed to ${action} company.`)
  }
}

const handleDrive = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_drive/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    fetchPending(); fetchStats();
  } catch (error) {
    alert(`Failed to ${action} drive.`)
  }
}

const toggleBlacklist = async (id) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/toggle_blacklist/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } })
    fetchUsers() 
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
  fetchUsers()
})
</script>