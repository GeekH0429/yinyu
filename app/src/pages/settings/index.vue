<template>
  <view class="settings">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <!-- 自定义导航栏 -->
    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title">设置</text>
      <view class="nav-placeholder"></view>
    </view>

    <!-- 个人资料分组 -->
    <text class="group-title anim-rise">个人资料</text>
    <view class="card group anim-rise delay-1">
      <!-- 头像 -->
      <view class="row" @tap="changeAvatar">
        <text class="row-label">头像</text>
        <view class="row-value">
          <CachedImage
            v-if="user && user.avatar_url"
            class="avatar"
            :src="user.avatar_url"
            mode="aspectFill"
          />
          <view v-else class="avatar placeholder">
            {{ (user?.nickname || user?.username || '?').slice(0, 1) }}
          </view>
          <text class="row-arrow">›</text>
        </view>
      </view>
      <!-- 昵称 -->
      <view class="row" @tap="editField('nickname')">
        <text class="row-label">昵称</text>
        <view class="row-value">
          <text class="row-text">{{ user?.nickname || '未设置' }}</text>
          <text class="row-arrow">›</text>
        </view>
      </view>
      <!-- 简介 -->
      <view class="row" @tap="editField('bio')">
        <text class="row-label">简介</text>
        <view class="row-value">
          <text class="row-text ellipsis">{{ user?.bio || '这个角落还很安静' }}</text>
          <text class="row-arrow">›</text>
        </view>
      </view>
      <!-- 邮箱 -->
      <view class="row" @tap="editField('email')">
        <text class="row-label">邮箱</text>
        <view class="row-value">
          <text class="row-text">{{ user?.email || '未绑定' }}</text>
          <text class="row-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 账号与安全分组 -->
    <text class="group-title anim-rise">账号与安全</text>
    <view class="card group anim-rise delay-1">
      <view class="row" @tap="openPwd">
        <text class="row-label">修改密码</text>
        <view class="row-value">
          <text class="row-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 显示分组:主题 + 字号 + 缓存 -->
    <text class="group-title anim-rise">显示与缓存</text>
    <view class="card group anim-rise delay-1">
      <view class="row" @tap="cycleTheme">
        <text class="row-label">主题</text>
        <view class="row-value">
          <text class="row-text">{{ themeLabel }}</text>
          <text class="row-arrow">›</text>
        </view>
      </view>
      <view class="row">
        <text class="row-label">动画效果</text>
        <view class="row-value">
          <switch
            class="anim-switch"
            :checked="animationsEnabled"
            color="#C4A882"
            @change="onAnimChange"
          />
        </view>
      </view>
      <view class="row font-row">
        <text class="row-label">阅读字号</text>
        <view class="row-font-controls">
          <text class="rf-letter sm">A</text>
          <slider
            class="rf-slider"
            :min="0"
            :max="FONT_LEVELS.length - 1"
            :step="1"
            :value="fontIdx"
            active-color="#C4A882"
            background-color="#EFE3D2"
            block-color="#C4A882"
            @changing="onFontChanging"
            @change="onFontChange"
          />
          <text class="rf-letter lg">A</text>
          <text class="rf-label">{{ fontLevel.label }}</text>
        </view>
      </view>
      <view class="row" @tap="clearCache">
        <text class="row-label">清除缓存</text>
        <view class="row-value">
          <text class="row-text">{{ cacheSizeText }}</text>
          <text class="row-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 关于分组 -->
    <text class="group-title anim-rise">关于</text>
    <view class="card group anim-rise delay-1">
      <view class="row">
        <text class="row-label">当前账号</text>
        <view class="row-value">
          <text class="row-text">{{ user?.username }}</text>
        </view>
      </view>
      <view class="row" v-if="user?.role === 'admin'">
        <text class="row-label">身份</text>
        <view class="row-value">
          <text class="row-text">管理员</text>
        </view>
      </view>
      <view class="row">
        <text class="row-label">版本</text>
        <view class="row-value">
          <text class="row-text">v1.0.0</text>
        </view>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="logout-btn pressable anim-rise" @tap="onLogout">
      <text>退出登录</text>
    </view>

    <!-- 修改密码弹窗 -->
    <view v-if="showPwd" class="mask" @tap="closePwd">
      <view class="dialog" :style="dialogStyle" @tap.stop>
        <text class="dialog-title">修改密码</text>
        <input class="dialog-input" v-model="pwdForm.old" password placeholder="当前密码" :cursor-spacing="20" />
        <input class="dialog-input" v-model="pwdForm.pwd" password placeholder="新密码(至少 6 位)" :cursor-spacing="20" />
        <input class="dialog-input" v-model="pwdForm.confirm" password placeholder="再次输入新密码" :cursor-spacing="20" />
        <view class="dialog-actions">
          <text class="dialog-btn cancel" @tap="closePwd">取消</text>
          <text class="dialog-btn confirm" @tap="submitPwd">确定</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onShow, onLoad, onUnload } from '@dcloudio/uni-app'
import { api } from '../../api'
import { getUser, logout } from '../../store/user'
import { themePref, setTheme, THEME_OPTIONS, animationsEnabled, setAnimationsEnabled } from '../../store/theme'
import { FONT_LEVELS, fontIdx, fontLevel, setFontIdxLive, setFontIdxCommit } from '../../store/readFont'
import { clearAllResourceCache, getCacheSize } from '../../utils/resourceCache'
import { clearArticleSnaps } from '../../utils/articleCache'
import { SNAP, clearSnap } from '../../utils/snap'
import CachedImage from '../../components/CachedImage.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const user = ref(getUser())

// 修改密码弹窗
const showPwd = ref(false)
const pwdForm = reactive({ old: '', pwd: '', confirm: '' })

// 软键盘高度:密码弹窗据此上移避开键盘(App/小程序;H5 该回调不触发,降级靠系统自适应)
const kbHeight = ref(0)
let kbCb = null
onLoad(() => {
  kbCb = (res) => (kbHeight.value = res.height || 0)
  uni.onKeyboardHeightChange(kbCb)
})
onUnload(() => {
  if (kbCb) uni.offKeyboardHeightChange(kbCb)
})
const dialogStyle = computed(() => ({
  transform: kbHeight.value ? `translateY(${-Math.round(kbHeight.value * 0.45)}px)` : 'translateY(0)',
  transition: 'transform 0.2s ease'
}))

onShow(() => {
  // 从编辑弹窗/其它操作返回时同步本地最新资料
  user.value = getUser()
  refreshCacheSize()
})

function goBack() {
  uni.navigateBack()
}

/* ---- 主题切换(跟随系统 / 浅色 / 深色) ---- */
const themeLabel = computed(() => {
  const opt = THEME_OPTIONS.find((o) => o.value === themePref.value)
  return opt ? opt.label : '跟随系统'
})
function cycleTheme() {
  uni.showActionSheet({
    itemList: THEME_OPTIONS.map((o) => o.label),
    success: (r) => {
      const opt = THEME_OPTIONS[r.tapIndex]
      if (opt) setTheme(opt.value)
    },
    fail: () => {
      /* 用户取消 */
    }
  })
}

/* ---- 动画开关(默认开;关闭后所有入场/反馈动画压成瞬态) ---- */
function onAnimChange(e) {
  setAnimationsEnabled(e.detail.value)
}

/* ---- 阅读字号(与阅读页 Aa 共用 store/readFont,任一处改动另一处自动同步) ---- */
function onFontChanging(e) {
  setFontIdxLive(e.detail.value)
}
function onFontChange(e) {
  setFontIdxCommit(e.detail.value)
}

/* ---- 缓存大小展示 + 一键清除 ---- */
const cacheBytes = ref(0)
const cacheSizeText = computed(() => {
  const b = cacheBytes.value
  if (!b) return '0 MB'
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + ' KB'
  return (b / 1024 / 1024).toFixed(1) + ' MB'
})
function refreshCacheSize() {
  cacheBytes.value = getCacheSize()
}
async function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '清除图片/音频本地缓存与列表快照?文章内容本身不会丢失。',
    confirmText: '清除',
    success: (r) => {
      if (!r.confirm) return
      uni.showLoading({ title: '清理中' })
      try {
        clearAllResourceCache() // App 端真正删沙箱文件
        clearArticleSnaps()
        clearSnap(SNAP.FEED)
        clearSnap(SNAP.ME)
        cacheBytes.value = 0
        uni.showToast({ title: '已清理', icon: 'success' })
      } finally {
        uni.hideLoading()
      }
    }
  })
}

// 各字段的弹窗配置
const FIELD_CONFIG = {
  nickname: { label: '昵称', placeholder: '请输入昵称' },
  bio: { label: '简介', placeholder: '写点什么介绍自己吧' },
  email: { label: '邮箱', placeholder: '请输入邮箱' }
}

function editField(field) {
  const cfg = FIELD_CONFIG[field]
  uni.showModal({
    title: '修改' + cfg.label,
    editable: true,
    placeholderText: cfg.placeholder,
    content: user.value?.[field] || '',
    success: async (r) => {
      if (!r.confirm) return
      const value = (r.content || '').trim()
      if (field === 'nickname' && !value) {
        uni.showToast({ title: '昵称不能为空', icon: 'none' })
        return
      }
      if (field === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
        return
      }
      try {
        const me = await api.me.update({ [field]: value })
        uni.setStorageSync('userInfo', me)
        user.value = me
        uni.showToast({ title: '已保存', icon: 'success' })
      } catch {
        /* request 拦截器已 toast */
      }
    }
  })
}

async function changeAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: async (res) => {
      const path = res.tempFilePaths && res.tempFilePaths[0]
      if (!path) return
      uni.showLoading({ title: '上传中' })
      try {
        const media = await api.upload(path)
        const me = await api.me.update({ avatar_url: media.url })
        uni.setStorageSync('userInfo', me)
        user.value = me
        uni.showToast({ title: '已更换', icon: 'success' })
      } catch {
        /* ignore */
      } finally {
        uni.hideLoading()
      }
    }
  })
}

function openPwd() {
  pwdForm.old = pwdForm.pwd = pwdForm.confirm = ''
  showPwd.value = true
}

function closePwd() {
  showPwd.value = false
}

function submitPwd() {
  const { old, pwd, confirm } = pwdForm
  if (!old || !pwd || !confirm) {
    uni.showToast({ title: '请填写完整', icon: 'none' })
    return
  }
  if (pwd.length < 6) {
    uni.showToast({ title: '新密码至少 6 位', icon: 'none' })
    return
  }
  if (pwd !== confirm) {
    uni.showToast({ title: '两次输入不一致', icon: 'none' })
    return
  }
  api.auth
    .changePassword(old, pwd)
    .then(() => {
      uni.showToast({ title: '密码已修改', icon: 'success' })
      closePwd()
    })
    .catch(() => {
      /* request 拦截器已 toast */
    })
}

function onLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要离开这个角落吗?',
    success: (r) => {
      if (!r.confirm) return
      logout()
      uni.reLaunch({ url: '/pages/login/index' })
    }
  })
}
</script>

<style scoped>
.settings {
  min-height: 100vh;
  background: #fdfbf7;
  padding-bottom: 80rpx;
}
.status-bar {
  width: 100%;
}
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 24rpx 12rpx 16rpx;
}
.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-back-icon {
  font-size: 56rpx;
  color: #c4a882;
  line-height: 1;
}
.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.nav-placeholder {
  width: 64rpx;
}
.group-title {
  display: block;
  margin: 36rpx 48rpx 16rpx;
  font-size: 24rpx;
  color: #b0b0b0;
}
.group {
  margin: 0 32rpx;
  overflow: hidden;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 26rpx 32rpx;
  border-bottom: 1rpx solid #f5f1ea;
}
.row:last-child {
  border-bottom: none;
}
.row-label {
  font-size: 30rpx;
  color: #4a4a4a;
  flex-shrink: 0;
}
.row-value {
  display: flex;
  align-items: center;
  margin-left: 24rpx;
}
.row-text {
  font-size: 28rpx;
  color: #8d8d8d;
  text-align: right;
}
.row-text.ellipsis {
  max-width: 360rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.row-arrow {
  margin-left: 14rpx;
  font-size: 40rpx;
  color: #d8d8d8;
  line-height: 1;
}
.anim-switch {
  transform: scale(0.85);
  margin-right: -8rpx;
}
/* 阅读字号行:label 在左,滑块控件组占满右侧 */
.font-row {
  align-items: center;
}
.row-font-controls {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-left: 24rpx;
}
.rf-letter {
  color: #c4a882;
  font-weight: 700;
  flex-shrink: 0;
}
.rf-letter.sm { font-size: 24rpx; }
.rf-letter.lg { font-size: 38rpx; }
.rf-slider {
  flex: 1;
  margin: 0 4rpx;
}
/* 当前档位名称固定宽度,避免 1 字 ↔ 2 字切换时挤动布局 */
.rf-label {
  font-size: 26rpx;
  color: #c4a882;
  font-weight: 600;
  min-width: 64rpx;
  text-align: center;
  flex-shrink: 0;
}
.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 44rpx;
}
.avatar.placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.logout-btn {
  margin: 64rpx 32rpx 0;
  padding: 30rpx 0;
  text-align: center;
  background: #fff;
  border-radius: 40rpx;
  color: #e8a0a0;
  font-size: 30rpx;
  box-shadow: 0 8rpx 32rpx rgba(232, 160, 160, 0.16);
}

/* 修改密码弹窗 */
.mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dialog {
  width: 600rpx;
  background: #fff;
  border-radius: 28rpx;
  padding: 40rpx;
}
.dialog-title {
  display: block;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #4a4a4a;
  margin-bottom: 32rpx;
}
.dialog-input {
  width: 100%;
  height: 84rpx;
  background: #f8f5f0;
  border-radius: 20rpx;
  padding: 0 24rpx;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}
.dialog-actions {
  display: flex;
  margin-top: 12rpx;
}
.dialog-btn {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  border-radius: 20rpx;
  font-size: 30rpx;
}
.dialog-btn.cancel {
  color: #8d8d8d;
  background: #f3eee5;
  margin-right: 20rpx;
}
.dialog-btn.confirm {
  color: #fff;
  background: linear-gradient(135deg, rgba(196, 168, 130, 0.95), rgba(196, 168, 130, 0.85));
}
</style>
