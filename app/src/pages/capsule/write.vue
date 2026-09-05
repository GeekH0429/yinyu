<template>
  <view class="cw" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="topbar-title serif">封存一封信</text>
      <view class="topbar-right"></view>
    </view>

    <view class="body">
      <input
        class="title-input"
        type="text"
        v-model="title"
        maxlength="200"
        placeholder="给这封信起个名字(可留空)"
        placeholder-style="color:#c8c0b2;"
      />

      <textarea
        class="content-input serif"
        v-model="content"
        :maxlength="20000"
        placeholder="写给未来的自己……

此刻的心情、正在经历的事、想说的话,
都封进这枚胶囊里。"
        placeholder-style="color:#c8c0b2;"
        :auto-height="false"
        :show-confirm-bar="false"
        :adjust-position="true"
      />

      <view class="date-area">
        <text class="date-label">什么时候开启</text>
        <view class="preset-row">
          <text
            v-for="p in presets"
            :key="p.label"
            :class="['preset', { chosen: chosen === p.label }]"
            @tap="choosePreset(p)"
          >{{ p.label }}</text>
        </view>
        <view :class="['custom-row', { chosen: chosen === '自选日期' }]" @tap="chooseCustom">
          <text class="custom-label">自选日期</text>
          <picker mode="date" :value="customDate" :start="todayStr" @change="onDateChange">
            <text class="custom-date">{{ customDate || '选择那一天' }}</text>
          </picker>
        </view>
        <text class="date-hint" v-if="unlockAtText">将于 {{ unlockAtText }} 开启</text>
      </view>

      <view class="seal-btn pressable" :class="{ disabled: !canSeal || sealing }" @tap="onSeal">
        <text class="seal-text">{{ sealing ? '封存中…' : '🔒 封存' }}</text>
      </view>
      <text class="seal-hint">封存后不可修改,删除即永远无法开启</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import { formatDate, formatTime } from '../../utils/format'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

const title = ref('')
const content = ref('')
const chosen = ref('一个月后') // 默认选一个预设
const customDate = ref('')
const sealing = ref(false)

const DAY = 86400000
const presets = [
  { label: '一周后', days: 7 },
  { label: '一个月后', days: 30 },
  { label: '三个月后', days: 90 },
  { label: '一年后', days: 365 }
]

const todayStr = formatDate(Date.now()) // 北京时间的今天

// 计算开启时间:预设按天数;自选按当天北京时间 08:00
const unlockAt = computed(() => {
  if (chosen.value === '自选日期') {
    if (!customDate.value) return null
    // 允许选今天:今天 08:00 可能已过 → 顺延到明天 08:00,保证 > now + 10min
    const d = new Date(customDate.value + 'T08:00:00+08:00')
    if (d.getTime() < Date.now() + 20 * 60 * 1000) d.setTime(d.getTime() + DAY)
    return d
  }
  const p = presets.find((x) => x.label === chosen.value)
  return p ? new Date(Date.now() + p.days * DAY) : null
})

const unlockAtText = computed(() => {
  const d = unlockAt.value
  return d ? formatTime(d) : '' // 北京时间 YYYY-MM-DD HH:mm
})

const canSeal = computed(() => content.value.trim() && unlockAt.value)

function choosePreset(p) {
  chosen.value = p.label
}
function chooseCustom() {
  chosen.value = '自选日期'
}
function onDateChange(e) {
  customDate.value = e.detail.value
  chosen.value = '自选日期'
}

function onSeal() {
  if (!canSeal.value || sealing.value) return
  uni.showModal({
    title: '封存这封信',
    content: '将于 ' + unlockAtText.value + ' 开启,封存后不可修改。确定吗?',
    confirmText: '封存',
    confirmColor: '#c4a882',
    success: (r) => {
      if (r.confirm) seal()
    }
  })
}

async function seal() {
  sealing.value = true
  try {
    await api.capsules.create({
      title: title.value.trim() || null,
      content: content.value.trim(),
      unlock_at: unlockAt.value.toISOString()
    })
    uni.showToast({ title: '已封存,未来见 ✦', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 800)
  } catch {
    /* request 层已 toast */
  } finally {
    sealing.value = false
  }
}

function goBack() {
  if (content.value.trim()) {
    uni.showModal({
      title: '还没封存',
      content: '退出后这封信不会被保存,确定离开吗?',
      confirmText: '离开',
      confirmColor: '#e0a8b0',
      success: (r) => {
        if (r.confirm) uni.navigateBack()
      }
    })
    return
  }
  uni.navigateBack()
}
</script>

<style scoped>
.cw {
  min-height: 100vh;
  background: #fdfbf7;
}
.status-bar {
  width: 100%;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 40rpx 8rpx;
}
.back {
  width: 120rpx;
  color: #c4a882;
  font-size: 30rpx;
}
.topbar-title {
  font-size: 32rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.topbar-right {
  width: 120rpx;
}
.body {
  padding: 24rpx 48rpx 120rpx;
}
.title-input {
  font-size: 32rpx;
  color: #4a4a4a;
  padding: 24rpx 32rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 4rpx 24rpx rgba(196, 168, 130, 0.1);
}
.content-input {
  width: 100%;
  box-sizing: border-box;
  height: 460rpx;
  margin-top: 24rpx;
  padding: 32rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 4rpx 24rpx rgba(196, 168, 130, 0.1);
  font-size: 30rpx;
  line-height: 1.8;
  color: #4a4a4a;
}
.date-area {
  margin-top: 32rpx;
  padding: 32rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 4rpx 24rpx rgba(196, 168, 130, 0.1);
}
.date-label {
  font-size: 26rpx;
  color: #8d8d8d;
  font-weight: 500;
}
.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  margin-top: 22rpx;
}
.preset {
  padding: 14rpx 30rpx;
  border-radius: 40rpx;
  background: #f3eee5;
  color: #8d8d8d;
  font-size: 26rpx;
}
.preset.chosen {
  background: rgba(196, 168, 130, 0.18);
  color: #c4a882;
  font-weight: 600;
}
.custom-row {
  margin-top: 20rpx;
  padding: 20rpx 28rpx;
  border-radius: 24rpx;
  background: #f3eee5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.custom-row.chosen {
  background: rgba(196, 168, 130, 0.18);
}
.custom-label {
  font-size: 26rpx;
  color: #8d8d8d;
}
.custom-row.chosen .custom-label {
  color: #c4a882;
  font-weight: 600;
}
.custom-date {
  font-size: 26rpx;
  color: #c4a882;
}
.date-hint {
  display: block;
  margin-top: 18rpx;
  font-size: 22rpx;
  color: #c4a882;
}
.seal-btn {
  margin-top: 48rpx;
  padding: 26rpx 0;
  border-radius: 48rpx;
  background: #c4a882;
  box-shadow: 0 8rpx 32rpx rgba(196, 168, 130, 0.4);
  text-align: center;
}
.seal-btn.disabled {
  opacity: 0.45;
}
.seal-text {
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
}
.seal-hint {
  display: block;
  text-align: center;
  margin-top: 18rpx;
  font-size: 22rpx;
  color: #b8b8b8;
}
</style>
