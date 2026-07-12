<template>
  <div>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4 shadow-sm">
      <div class="container">
        <span class="navbar-brand fw-bold text-primary">Placement Portal V2 | Admin Command Center</span>
        <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>

    <div class="container">
      
      <div class="row mb-5">
        <div class="col-12">
          <div class="card shadow-sm bg-dark border-secondary">
            <div class="card-header border-secondary text-light fw-bold">
              Platform Analytics Overview
            </div>
            <div class="card-body" style="height: 350px;">
              <Bar
                v-if="isChartLoaded"
                id="my-chart-id"
                :options="chartOptions"
                :data="chartData"
              />
              <div v-else class="text-center text-muted mt-5">
                Loading analytics...
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-6 mb-4">
          <h5 class="mb-3">Pending Company Approvals</h5>
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              <div v-if="pendingCompanies.length === 0" class="p-4 text-muted text-center">
                No pending companies.
              </div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Company Name</th>
                    <th class="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="company in pendingCompanies" :key="company.id">
                    <td class="align-middle fw-bold text-info">{{ company.username }}</td>
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
          <h5 class="mb-3">Pending Drive Approvals</h5>
          <div class="card shadow-sm bg-dark text-light border-secondary">
            <div class="card-body p-0">
              <div v-if="pendingDrives.length === 0" class="p-4 text-muted text-center">
                No pending drives.
              </div>
              <table v-else class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th>Job Title</th>
                    <th class="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in pendingDrives" :key="drive.id">
                    <td class="align-middle text-warning fw-bold">{{ drive.job_title }}</td>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
// Import Chart.js components
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

// Register Chart.js elements
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const router = useRouter()
const API_URL = 'http://127.0.0.1:5000/api'

// --- State Variables ---
const pendingCompanies = ref([])
const pendingDrives = ref([])
const isChartLoaded = ref(false)

// --- Chart Data & Configuration ---
const chartData = ref({
  labels: ['Students', 'Companies', 'Drives', 'Applications'],
  datasets: [{
    label: 'Total Count',
    // Custom colors for each bar to make it pop!
    backgroundColor: ['#42b883', '#ffc107', '#0dcaf0', '#0d6efd'],
    data: [0, 0, 0, 0] 
  }]
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false } // Hides the legend since the labels are self-explanatory
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { stepSize: 1, color: '#adb5bd' },
      grid: { color: '#495057' }
    },
    x: {
      ticks: { color: '#adb5bd' },
      grid: { display: false }
    }
  }
})

// --- API Calls ---

const fetchStats = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`${API_URL}/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    // Inject the real data from Flask into the chart
    const stats = res.data.data
    chartData.value.datasets[0].data = [
      stats.total_students, 
      stats.total_companies, 
      stats.total_drives, 
      stats.total_applications
    ]
    
    // Tell Vue it is safe to render the chart now
    isChartLoaded.value = true
  } catch (error) {
    console.error("Failed to fetch stats", error)
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

const handleCompany = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_company/${id}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchPending() // Refresh the list
    fetchStats()   // Refresh the chart!
  } catch (error) {
    alert(`Failed to ${action} company.`)
  }
}

const handleDrive = async (id, action) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`${API_URL}/admin/${action}_drive/${id}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchPending()
    fetchStats()
  } catch (error) {
    alert(`Failed to ${action} drive.`)
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

// Fetch everything when the page loads
onMounted(() => {
  fetchStats()
  fetchPending()
})
</script>