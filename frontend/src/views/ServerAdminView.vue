<template>
  <div class="min-h-screen bg-[#f7f7f7] py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <!-- Top Nav -->
      <div class="flex items-center justify-between pb-6 mb-6 border-b border-gray-200/60">
        <div class="flex items-center gap-4">
          <router-link
            to="/servers"
            class="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Servers
          </router-link>
          <span class="text-gray-300">/</span>
          <router-link
            to="/dashboard"
            class="text-xs font-semibold text-gray-500 hover:text-gray-900 transition"
          >
            Dashboard
          </router-link>
        </div>

        <button
          @click="loadAll"
          :disabled="loading"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-[#833dff] hover:text-[#722ce6] transition cursor-pointer disabled:opacity-50"
        >
          <svg
            class="w-3.5 h-3.5"
            :class="{ 'animate-spin': loading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Data
        </button>
      </div>

      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-purple-100 text-[#833dff] mb-3 shadow-2xs">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          Server Administration
        </h1>
        <p class="mt-1.5 text-xs sm:text-sm text-gray-500 max-w-lg mx-auto">
          Manage user permissions, roles, and invitation links for <strong class="text-gray-800">{{ activeServer?.name || 'Current Server' }}</strong>.
        </p>
      </div>

      <!-- Toast Message -->
      <div
        v-if="toastMessage"
        class="mb-6 p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl flex items-center justify-between border border-emerald-200 animate-fade-in shadow-2xs"
      >
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-emerald-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>{{ toastMessage }}</span>
        </div>
        <button @click="toastMessage = ''" class="text-emerald-500 hover:text-emerald-700 text-sm font-bold border-0 bg-transparent">&times;</button>
      </div>

      <!-- Error Message -->
      <div
        v-if="errorMessage"
        class="mb-6 p-3 bg-red-50 text-red-700 text-xs rounded-xl flex items-center justify-between border border-red-200 animate-fade-in shadow-2xs"
      >
        <span>{{ errorMessage }}</span>
        <button @click="errorMessage = ''" class="text-red-500 hover:text-red-700 text-sm font-bold border-0 bg-transparent">&times;</button>
      </div>

      <!-- Auth Disabled Warning (Informational) -->
      <div
        v-if="!state.auth?.enabled"
        class="mb-6 p-4 bg-amber-50/80 rounded-2xl border border-amber-200/80 text-amber-900 text-xs shadow-2xs"
      >
        <div class="flex items-start gap-3">
          <svg class="w-5 h-5 text-amber-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <span class="font-bold">Authentication is currently disabled on this server</span>
            <p class="mt-1 text-amber-800 leading-relaxed">
              All connected clients operate with full unrestricted access. To enforce role-based access control (Viewer, Editor, Admin), start the server with the <code class="bg-amber-100/70 px-1 py-0.5 rounded font-mono text-amber-900 font-bold">--auth</code> flag.
            </p>
          </div>
        </div>
      </div>

      <!-- Access Denied if not Admin -->
      <div
        v-if="state.auth?.enabled && !isAdmin"
        class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center max-w-md mx-auto my-8"
      >
        <div class="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h2 class="text-base font-bold text-gray-900 mb-1">Administrator Access Required</h2>
        <p class="text-xs text-gray-500 mb-4 leading-relaxed">
          You are currently signed in as <strong class="text-gray-800">{{ state.auth?.user?.username }}</strong> with role <strong class="uppercase text-[#833dff]">{{ state.auth?.user?.role }}</strong>. You need an Admin account to manage server users and invitations.
        </p>
        <button
          @click="state.auth.showLoginModal = true"
          class="px-4 py-2 bg-[#833dff] hover:bg-[#722ce6] text-white rounded-xl text-xs font-semibold transition shadow-2xs border-0 cursor-pointer"
        >
          Sign in as Administrator
        </button>
      </div>

      <!-- Admin Content -->
      <div v-else class="space-y-8">
        <!-- Section 1: Users & Roles Management -->
        <div class="bg-white rounded-2xl shadow-2xs border border-gray-100 overflow-hidden">
          <div class="p-5 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
            <div>
              <h2 class="text-sm font-bold text-gray-900">User Roles & Access Control</h2>
              <p class="text-xs text-gray-500 mt-0.5">Assign Viewer, Editor, or Admin roles to registered users.</p>
            </div>
            <span class="text-xs font-mono bg-purple-50 text-[#833dff] px-2.5 py-1 rounded-lg font-semibold">
              {{ users.length }} {{ users.length === 1 ? 'user' : 'users' }}
            </span>
          </div>

          <!-- Users Table -->
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-gray-50/70 border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th class="py-3 px-4">Username</th>
                  <th class="py-3 px-4">Role</th>
                  <th class="py-3 px-4">Created</th>
                  <th class="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="user in users" :key="user.id" class="hover:bg-purple-50/20 transition">
                  <td class="py-3.5 px-4">
                    <div class="flex items-center gap-2">
                      <div class="w-7 h-7 rounded-lg bg-gray-100 text-gray-700 font-bold flex items-center justify-center text-xs">
                        {{ user.username.charAt(0).toUpperCase() }}
                      </div>
                      <div>
                        <span class="font-semibold text-gray-900">{{ user.username }}</span>
                        <span
                          v-if="user.id === state.auth?.user?.id"
                          class="ml-1.5 px-1.5 py-0.2 rounded text-[10px] bg-purple-100 text-[#833dff] font-medium"
                        >
                          You
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="py-3.5 px-4">
                    <select
                      :value="user.role"
                      @change="handleRoleChange(user, $event.target.value)"
                      :disabled="user.id === state.auth?.user?.id && user.role === 'admin'"
                      class="px-2.5 py-1 rounded-lg border border-gray-200 text-xs font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-[#833dff]/20 focus:border-[#833dff] cursor-pointer"
                      :class="roleBadgeTextClass(user.role)"
                    >
                      <option value="viewer">Viewer (Read-only)</option>
                      <option value="editor">Editor (Modify reports)</option>
                      <option value="admin">Admin (Full privileges)</option>
                    </select>
                  </td>
                  <td class="py-3.5 px-4 text-gray-500 font-mono text-[11px]">
                    {{ formatDateTime(user.created_at) }}
                  </td>
                  <td class="py-3.5 px-4 text-right">
                    <button
                      @click="handleDeleteUser(user)"
                      :disabled="user.id === state.auth?.user?.id"
                      class="px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition border-0 bg-transparent cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                      :title="user.id === state.auth?.user?.id ? 'Cannot delete your own account' : 'Delete user account'"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
                <tr v-if="users.length === 0">
                  <td colspan="4" class="py-6 text-center text-gray-400">
                    No users registered yet. Generate an invitation below to onboard team members.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 2: Invitation Tokens Generator & Manager -->
        <div class="bg-white rounded-2xl shadow-2xs border border-gray-100 overflow-hidden">
          <div class="p-5 border-b border-gray-100">
            <h2 class="text-sm font-bold text-gray-900">Generate Invitation Token</h2>
            <p class="text-xs text-gray-500 mt-0.5">Invite new team members with specific roles and optional expiration.</p>

            <!-- Invite Creation Form -->
            <form @submit.prevent="handleCreateInvite" class="mt-4 grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label class="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Role
                </label>
                <select
                  v-model="newInvite.role"
                  class="w-full px-3.5 py-2.5 bg-gray-100/70 focus:bg-white rounded-xl text-xs text-gray-900 border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff]/25 shadow-2xs cursor-pointer"
                >
                  <option value="viewer">Viewer (Read-only)</option>
                  <option value="editor">Editor (Modify reports)</option>
                  <option value="admin">Admin (Full privileges)</option>
                </select>
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Expiration
                </label>
                <select
                  v-model="newInvite.expiresHours"
                  class="w-full px-3.5 py-2.5 bg-gray-100/70 focus:bg-white rounded-xl text-xs text-gray-900 border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff]/25 shadow-2xs cursor-pointer"
                >
                  <option :value="1">1 Hour</option>
                  <option :value="24">24 Hours (1 day)</option>
                  <option :value="168">7 Days (1 week)</option>
                  <option :value="720">30 Days (1 month)</option>
                  <option :value="null">Never expires</option>
                </select>
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Max Uses
                </label>
                <input
                  v-model.number="newInvite.maxUses"
                  type="number"
                  min="1"
                  placeholder="1 (Single-use)"
                  class="w-full px-3.5 py-2.5 bg-gray-100/70 focus:bg-white rounded-xl text-xs text-gray-900 border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff]/25 shadow-2xs"
                />
              </div>

              <div class="flex items-end">
                <button
                  type="submit"
                  :disabled="creatingInvite"
                  class="w-full px-4 py-2 rounded-xl text-xs font-semibold bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5 border-0"
                >
                  <span v-if="creatingInvite" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Create Invite</span>
                </button>
              </div>
            </form>

            <!-- Newly created invite banner -->
            <div
              v-if="latestCreatedInvite"
              class="mt-4 p-3.5 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-900 animate-fade-in"
            >
              <div class="flex items-center justify-between mb-1.5">
                <span class="font-bold flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  Invitation Link Generated
                </span>
                <button
                  @click="copyInviteLink(latestCreatedInvite.token)"
                  class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-xs transition cursor-pointer border-0 shadow-2xs"
                >
                  {{ copiedToken === latestCreatedInvite.token ? 'Copied!' : 'Copy Link' }}
                </button>
              </div>
              <div class="font-mono text-[11px] bg-white/80 p-2 rounded-lg break-all text-emerald-800 border border-emerald-100">
                {{ formatInviteUrl(latestCreatedInvite.token) }}
              </div>
            </div>
          </div>

          <!-- Active Invites List Header -->
          <div class="p-4 bg-gray-50/50 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">Active Invitation Tokens</h3>
            <span class="text-xs text-gray-500 font-mono">{{ invites.length }} tokens</span>
          </div>

          <!-- Invites Table -->
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-gray-50/70 border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th class="py-3 px-4">Token & Invite Link</th>
                  <th class="py-3 px-4">Role</th>
                  <th class="py-3 px-4">Uses</th>
                  <th class="py-3 px-4">Expires</th>
                  <th class="py-3 px-4">Created</th>
                  <th class="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="inv in invites" :key="inv.token" class="hover:bg-purple-50/20 transition">
                  <td class="py-3.5 px-4">
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-[11px] text-gray-800 font-medium" :title="inv.token">
                        {{ inv.token.substring(0, 10) }}...
                      </span>
                      <button
                        @click="copyInviteLink(inv.token)"
                        class="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 hover:bg-purple-100 text-[#833dff] transition border-0 cursor-pointer"
                        title="Copy full invite link"
                      >
                        {{ copiedToken === inv.token ? 'Copied!' : 'Copy' }}
                      </button>
                    </div>
                  </td>
                  <td class="py-3.5 px-4">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                      :class="roleBadgeClass(inv.role)"
                    >
                      {{ inv.role }}
                    </span>
                  </td>
                  <td class="py-3.5 px-4 text-gray-600 font-mono text-[11px]">
                    {{ inv.uses_count }} / {{ inv.max_uses ? inv.max_uses : '∞' }}
                  </td>
                  <td class="py-3.5 px-4 text-[11px]">
                    <span v-if="isInviteExpired(inv)" class="text-red-600 font-semibold">
                      Expired
                    </span>
                    <span v-else-if="inv.expires_at" class="text-gray-600 font-mono">
                      {{ formatExpiry(inv.expires_at) }}
                    </span>
                    <span v-else class="text-emerald-600 font-semibold">
                      Never
                    </span>
                  </td>
                  <td class="py-3.5 px-4 text-gray-400 font-mono text-[11px]">
                    {{ formatDateTime(inv.created_at) }}
                  </td>
                  <td class="py-3.5 px-4 text-right">
                    <button
                      @click="handleRevokeInvite(inv)"
                      class="px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition border-0 bg-transparent cursor-pointer"
                      title="Revoke invitation immediately"
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
                <tr v-if="invites.length === 0">
                  <td colspan="6" class="py-6 text-center text-gray-400">
                    No active invitation tokens. Create one above.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 3: Server Configuration & Details -->
        <div class="bg-white rounded-2xl p-5 shadow-2xs border border-gray-100">
          <h2 class="text-sm font-bold text-gray-900 mb-3">Server Configuration</h2>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div class="p-3 bg-gray-50 rounded-xl">
              <span class="text-gray-400 block mb-1">Reports Directory</span>
              <span class="font-mono text-gray-800 font-medium break-all">{{ serverConfig?.base_dir || 'N/A' }}</span>
            </div>
            <div class="p-3 bg-gray-50 rounded-xl">
              <span class="text-gray-400 block mb-1">Authentication</span>
              <span class="font-semibold" :class="serverConfig?.auth_enabled ? 'text-emerald-600' : 'text-amber-600'">
                {{ serverConfig?.auth_enabled ? 'Active (RBAC Enforced)' : 'Disabled (Public)' }}
              </span>
            </div>
            <div class="p-3 bg-gray-50 rounded-xl">
              <span class="text-gray-400 block mb-1">Total Reports</span>
              <span class="font-mono text-gray-800 font-semibold">{{ serverConfig?.reports_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  state,
  isAdmin,
  getActiveServerUrl
} from '../store.js'
import {
  apiGetAdminUsers,
  apiUpdateUserRole,
  apiDeleteUser,
  apiGetAdminInvites,
  apiCreateInvite,
  apiDeleteInvite,
  apiGetAdminConfig
} from '../api.js'

const loading = ref(false)
const toastMessage = ref('')
const errorMessage = ref('')

const users = ref([])
const invites = ref([])
const serverConfig = ref(null)

const activeServer = computed(() => state.activeServer)

const newInvite = reactive({
  role: 'viewer',
  expiresHours: 24,
  maxUses: 1
})
const creatingInvite = ref(false)
const latestCreatedInvite = ref(null)
const copiedToken = ref(null)

function roleBadgeClass(role) {
  switch (role) {
    case 'admin':
      return 'bg-purple-100 text-[#833dff]'
    case 'editor':
      return 'bg-blue-100 text-blue-800'
    case 'viewer':
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function roleBadgeTextClass(role) {
  switch (role) {
    case 'admin':
      return 'text-[#833dff] font-bold'
    case 'editor':
      return 'text-blue-700 font-bold'
    case 'viewer':
    default:
      return 'text-gray-700'
  }
}

function formatDateTime(isoString) {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}

function formatExpiry(isoString) {
  if (!isoString) return 'Never'
  try {
    const d = new Date(isoString)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}

function isInviteExpired(inv) {
  if (!inv.expires_at) return false
  return new Date(inv.expires_at) < new Date()
}

function formatInviteUrl(token) {
  const base = getActiveServerUrl(state.activeServer) || window.location.origin
  return `${base}/#/invite?token=${encodeURIComponent(token)}`
}

async function copyInviteLink(token) {
  const url = formatInviteUrl(token)
  try {
    await navigator.clipboard.writeText(url)
    copiedToken.value = token
    toastMessage.value = 'Invitation link copied to clipboard.'
    setTimeout(() => {
      if (copiedToken.value === token) copiedToken.value = null
    }, 3000)
  } catch {
    toastMessage.value = `Link: ${url}`
  }
}

async function loadAll() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [uRes, iRes, cRes] = await Promise.all([
      apiGetAdminUsers(),
      apiGetAdminInvites(),
      apiGetAdminConfig()
    ])

    if (uRes.ok) {
      users.value = await uRes.json()
    } else if (uRes.status === 403 || uRes.status === 401) {
      errorMessage.value = 'Admin permissions required to view user list.'
    }

    if (iRes.ok) {
      invites.value = await iRes.json()
    }

    if (cRes.ok) {
      serverConfig.value = await cRes.json()
    }
  } catch (err) {
    errorMessage.value = err.message || 'Failed to load administration data.'
  } finally {
    loading.value = false
  }
}

async function handleRoleChange(user, newRole) {
  try {
    const res = await apiUpdateUserRole(user.id, newRole)
    if (res.ok) {
      user.role = newRole
      toastMessage.value = `Role for ${user.username} updated to ${newRole}.`
    } else {
      const err = await res.json().catch(() => ({}))
      errorMessage.value = err.detail || 'Failed to update user role.'
    }
  } catch (err) {
    errorMessage.value = err.message || 'Could not update user role.'
  }
}

async function handleDeleteUser(user) {
  if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) return
  try {
    const res = await apiDeleteUser(user.id)
    if (res.ok) {
      users.value = users.value.filter(u => u.id !== user.id)
      toastMessage.value = `User ${user.username} removed.`
    } else {
      const err = await res.json().catch(() => ({}))
      errorMessage.value = err.detail || 'Failed to delete user.'
    }
  } catch (err) {
    errorMessage.value = err.message || 'Could not delete user.'
  }
}

async function handleCreateInvite() {
  creatingInvite.value = true
  errorMessage.value = ''
  try {
    const payload = {
      role: newInvite.role,
      expires_hours: newInvite.expiresHours,
      max_uses: newInvite.maxUses || null
    }
    const res = await apiCreateInvite(payload)
    if (res.ok) {
      const data = await res.json()
      latestCreatedInvite.value = data
      invites.value.unshift(data)
      toastMessage.value = `Invitation token created with ${data.role} privileges.`
    } else {
      const err = await res.json().catch(() => ({}))
      errorMessage.value = err.detail || 'Failed to create invitation.'
    }
  } catch (err) {
    errorMessage.value = err.message || 'Could not create invitation token.'
  } finally {
    creatingInvite.value = false
  }
}

async function handleRevokeInvite(inv) {
  if (!confirm(`Revoke invitation token "${inv.token.substring(0, 8)}..."?`)) return
  try {
    const res = await apiDeleteInvite(inv.token)
    if (res.ok) {
      invites.value = invites.value.filter(i => i.token !== inv.token)
      if (latestCreatedInvite.value?.token === inv.token) {
        latestCreatedInvite.value = null
      }
      toastMessage.value = 'Invitation token revoked.'
    } else {
      const err = await res.json().catch(() => ({}))
      errorMessage.value = err.detail || 'Failed to revoke invite.'
    }
  } catch (err) {
    errorMessage.value = err.message || 'Could not revoke invite.'
  }
}

onMounted(() => {
  loadAll()
})
</script>
