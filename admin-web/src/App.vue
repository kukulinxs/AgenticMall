<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, EditPen, Plus, Refresh, Search, Top, Bottom } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createGoods, listGoods, removeGoods, setGoodsStatus, updateGoods } from './api'

const loading = ref(false)
const goods = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const filters = reactive({ name: '', department: '', status: '' })
const form = reactive(emptyForm())

const onlineCount = computed(() => goods.value.filter((item) => item.status === 'online').length)
const totalStock = computed(() => goods.value.reduce((total, item) => total + item.stock, 0))

function emptyForm() {
  return { name: '', price: 0, stock: 0, department: '', description: '' }
}

function resetForm() {
  Object.assign(form, emptyForm())
}

function formatDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleString('zh-CN', { hour12: false })
}

async function loadGoods() {
  loading.value = true
  try {
    goods.value = await listGoods(filters)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { name: '', department: '', status: '' })
  loadGoods()
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(goodsItem) {
  editingId.value = goodsItem.id
  Object.assign(form, {
    name: goodsItem.name,
    price: goodsItem.price,
    stock: goodsItem.stock,
    department: goodsItem.department,
    description: goodsItem.description
  })
  dialogVisible.value = true
}

async function saveGoods() {
  if (!form.name.trim() || !form.department.trim() || form.price <= 0 || form.stock < 0) {
    ElMessage.warning('请填写名称、所属部门，并确保价格和库存有效')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateGoods({ goods_id: editingId.value, price: Number(form.price), stock: Number(form.stock), department: form.department.trim(), description: form.description })
      ElMessage.success('商品已更新')
    } else {
      await createGoods({ name: form.name.trim(), price: Number(form.price), stock: Number(form.stock), department: form.department.trim(), description: form.description })
      ElMessage.success('商品已创建')
    }
    dialogVisible.value = false
    await loadGoods()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

async function toggleStatus(goodsItem) {
  const targetStatus = goodsItem.status === 'online' ? 'offline' : 'online'
  try {
    await setGoodsStatus(goodsItem.id, targetStatus)
    ElMessage.success(targetStatus === 'online' ? '商品已上架' : '商品已下架')
    await loadGoods()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function deleteGoods(goodsItem) {
  try {
    await ElMessageBox.confirm(`确认删除“${goodsItem.name}”吗？`, '删除商品', { type: 'warning' })
    await removeGoods(goodsItem.id)
    ElMessage.success('商品已删除')
    await loadGoods()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message)
  }
}

onMounted(loadGoods)
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">T</span><span>TeleAgent</span></div>
      <p class="workspace-label">商品运营</p>
      <nav><a class="nav-item active">商品管理</a></nav>
      <div class="sidebar-footer"><span class="status-dot"></span>Mock 后台已连接</div>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div><p class="eyebrow">PRODUCT OPERATIONS</p><h1>商品管理</h1></div>
        <el-button :icon="Refresh" circle title="刷新商品列表" @click="loadGoods" />
      </header>

      <section class="metrics" aria-label="商品概览">
        <div class="metric"><span>当前商品</span><strong>{{ goods.length }}</strong><small>按当前筛选条件统计</small></div>
        <div class="metric"><span>已上架</span><strong>{{ onlineCount }}</strong><small>可供 Agent 查询与操作</small></div>
        <div class="metric"><span>库存总量</span><strong>{{ totalStock }}</strong><small>单位：件</small></div>
      </section>

      <section class="toolbar" aria-label="商品筛选">
        <el-input v-model="filters.name" clearable placeholder="商品名称" @keyup.enter="loadGoods" />
        <el-input v-model="filters.department" clearable placeholder="所属部门" @keyup.enter="loadGoods" />
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option label="已上架" value="online" />
          <el-option label="已下架" value="offline" />
        </el-select>
        <el-button :icon="Search" type="primary" @click="loadGoods">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <div class="toolbar-spacer"></div>
        <el-button :icon="Plus" type="primary" @click="openCreate">新增商品</el-button>
      </section>

      <section class="table-panel">
        <el-table v-loading="loading" :data="goods" style="width: 100%" empty-text="暂无符合条件的商品">
          <el-table-column label="商品" min-width="245">
            <template #default="{ row }"><div class="product-cell"><span class="product-icon">{{ row.name.slice(0, 1) }}</span><div><strong>{{ row.name }}</strong><small>{{ row.id }}</small></div></div></template>
          </el-table-column>
          <el-table-column label="所属部门" prop="department" min-width="130" />
          <el-table-column label="价格" min-width="110"><template #default="{ row }"><span class="price">¥{{ row.price.toFixed(2) }}</span></template></el-table-column>
          <el-table-column label="库存" prop="stock" min-width="90" />
          <el-table-column label="状态" min-width="105"><template #default="{ row }"><el-tag :type="row.status === 'online' ? 'success' : 'info'" effect="light">{{ row.status === 'online' ? '已上架' : '已下架' }}</el-tag></template></el-table-column>
          <el-table-column label="更新时间" min-width="175"><template #default="{ row }">{{ formatDate(row.create_time) }}</template></el-table-column>
          <el-table-column label="操作" fixed="right" min-width="220">
            <template #default="{ row }">
              <el-button :icon="EditPen" link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button :icon="row.status === 'online' ? Bottom : Top" link type="primary" @click="toggleStatus(row)">{{ row.status === 'online' ? '下架' : '上架' }}</el-button>
              <el-button :icon="Delete" link type="danger" @click="deleteGoods(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </section>
  </main>

  <el-dialog v-model="dialogVisible" :title="editingId ? '编辑商品' : '新增商品'" width="520px" @closed="resetForm">
    <el-form label-position="top">
      <el-form-item label="商品名称" required><el-input v-model="form.name" :disabled="Boolean(editingId)" placeholder="例如：华为Mate70" /></el-form-item>
      <div class="form-row"><el-form-item label="价格（元）" required><el-input-number v-model="form.price" :min="0.01" :precision="2" controls-position="right" /></el-form-item><el-form-item label="库存" required><el-input-number v-model="form.stock" :min="0" :max="99999" controls-position="right" /></el-form-item></div>
      <el-form-item label="所属部门" required><el-input v-model="form.department" placeholder="例如：手机事业部" /></el-form-item>
      <el-form-item label="商品描述"><el-input v-model="form.description" :rows="3" type="textarea" placeholder="选填" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button :loading="saving" type="primary" @click="saveGoods">保存</el-button></template>
  </el-dialog>
</template>
