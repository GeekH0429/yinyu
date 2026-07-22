<template>
  <view v-if="visible" class="aip-mask" @tap="close">
    <view class="aip-card" @tap.stop>
      <view class="aip-head">
        <text class="aip-title">音频信息</text>
        <text class="aip-close" @tap="close">✕</text>
      </view>

      <view class="aip-field">
        <text class="aip-label">音频名称</text>
        <input class="aip-input" v-model="title" placeholder="给这段音频起个名字(可选)" maxlength="100" />
      </view>

      <view class="aip-field">
        <text class="aip-label">歌手 / 来源</text>
        <input class="aip-input" v-model="artist" placeholder="谁的作品?(可选)" maxlength="60" />
      </view>

      <view class="aip-field">
        <text class="aip-label">封面图</text>
        <view class="aip-cover-row">
          <view v-if="cover" class="aip-cover-preview" @tap="chooseCover">
            <image class="aip-cover-img" :src="resourceUrl(cover)" mode="aspectFill" />
          </view>
          <text v-else class="aip-cover-add" @tap="chooseCover">+ 选择封面</text>
          <text v-if="cover" class="aip-cover-remove" @tap="cover = ''">移除</text>
          <text v-if="coverUploading" class="aip-tip">上传中…</text>
        </view>
      </view>

      <view class="aip-actions">
        <text class="aip-btn" @tap="close">取消</text>
        <text class="aip-btn primary" @tap="onConfirm">插入</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../api'
import { resourceUrl } from '../config'
import { chooseImage } from '../utils/pick'

const props = defineProps({
  visible: { type: Boolean, default: false },
  src: { type: String, default: '' }
})
const emit = defineEmits(['update:visible', 'confirm'])

const title = ref('')
const artist = ref('')
const cover = ref('')
const coverUploading = ref(false)

// 每次打开都重置(音频 src 由父组件通过 prop 传入)
watch(
  () => props.visible,
  (v) => {
    if (v) {
      title.value = ''
      artist.value = ''
      cover.value = ''
    }
  }
)

function close() {
  emit('update:visible', false)
}

async function chooseCover() {
  try {
    const path = await chooseImage()
    coverUploading.value = true
    cover.value = (await api.upload(path)).url
  } catch {
    /* 用户取消 */
  } finally {
    coverUploading.value = false
  }
}

function onConfirm() {
  emit('confirm', {
    src: props.src,
    title: title.value.trim(),
    artist: artist.value.trim(),
    cover: cover.value || null
  })
  close()
}
</script>

<style scoped>
.aip-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.aip-card {
  width: 600rpx;
  background: #fdfbf7;
  border-radius: 32rpx;
  padding: 40rpx 36rpx;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.2);
}
.aip-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28rpx;
}
.aip-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.aip-close {
  font-size: 36rpx;
  color: #b0b0b0;
  padding: 0 8rpx;
}
.aip-field {
  margin-bottom: 24rpx;
}
.aip-label {
  display: block;
  font-size: 24rpx;
  color: #8d8d8d;
  margin-bottom: 12rpx;
}
.aip-input {
  width: 100%;
  height: 76rpx;
  box-sizing: border-box;
  background: #fff;
  border: 2rpx solid #ece3d6;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #4a4a4a;
}
.aip-cover-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.aip-cover-preview {
  width: 120rpx;
  height: 120rpx;
  border-radius: 16rpx;
  overflow: hidden;
}
.aip-cover-img {
  width: 120rpx;
  height: 120rpx;
  display: block;
}
.aip-cover-add {
  padding: 16rpx 28rpx;
  background: #f3eee5;
  color: #88a07a;
  border-radius: 28rpx;
  font-size: 26rpx;
}
.aip-cover-remove {
  color: #d08a8a;
  font-size: 26rpx;
}
.aip-tip {
  color: #c4a882;
  font-size: 24rpx;
}
.aip-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 36rpx;
}
.aip-btn {
  flex: 1;
  height: 84rpx;
  line-height: 84rpx;
  text-align: center;
  border-radius: 42rpx;
  font-size: 30rpx;
  background: #f0ece4;
  color: #6a6a6a;
}
.aip-btn.primary {
  background: linear-gradient(135deg, #a8c09a 0%, #88a07a 100%);
  color: #fff;
}
</style>
