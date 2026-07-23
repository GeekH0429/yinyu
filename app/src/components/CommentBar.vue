<template>
  <view class="cmt-bar">
    <!-- @用户选择浮层 -->
    <view v-if="mentionPicker.visible" class="mention-pop">
      <view v-if="mentionPicker.loading" class="mention-hint">搜索中…</view>
      <view v-else-if="mentionPicker.results.length === 0" class="mention-hint">未找到用户</view>
      <scroll-view scroll-y class="mention-list">
        <view
          v-for="u in mentionPicker.results"
          :key="u.id"
          class="mention-item"
          @tap="pickMention(u)"
        >
          <image
            v-if="u.avatar_url"
            class="m-avatar"
            :src="u.avatar_url"
            mode="aspectFill"
          />
          <view v-else class="m-avatar placeholder">{{ (u.nickname || '?').slice(0, 1) }}</view>
          <text class="m-name">{{ u.nickname || u.id }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- 回复模式横幅 -->
    <view v-if="replyTarget" class="reply-banner">
      <text class="reply-text">
        回复 @{{ replyTarget.author?.nickname || '评论' }}
      </text>
      <text class="cancel" @tap="cancelReply">取消</text>
    </view>

    <view class="bar">
      <textarea
        class="input"
        v-model="text"
        :placeholder="placeholder"
        :maxlength="-1"
        auto-height
        :cursor-spacing="120"
        :adjust-position="true"
        :show-confirm-bar="false"
        :disable-default-padding="true"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
      />
      <view
        :class="['send-btn', { disabled: !canSend || sending }]"
        @tap="onSend"
      >
        <text>{{ sending ? '…' : '发送' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { api } from '../api'

const props = defineProps({
  articleId: { type: Number, required: true }
})

const emit = defineEmits(['sent', 'mention-shown'])

// 回复目标:顶层评论对象(含 id / author) — 由父组件设置
const replyTarget = ref(null)
// 当前 text
const text = ref('')
const sending = ref(false)
const focused = ref(false)

// 已选择的提及用户列表 [{id, nickname}]
const mentions = reactive([])

const placeholder = computed(() => {
  if (replyTarget.value) {
    return '回复 @' + (replyTarget.value.author?.nickname || '评论') + '…'
  }
  return '写下你的温柔…'
})

const canSend = computed(() => text.value.trim().length > 0)

// ---------- @提及选择器 ----------
const mentionPicker = reactive({
  visible: false,
  loading: false,
  results: [],
  prefix: '',
  startIndex: -1 // @ 在 text 中的位置
})
let searchTimer = null

// 检测光标前的 @word 模式(支持中英文、数字、下划线,不含空格)
function detectMention(t) {
  // 从末尾向前匹配:取最后一个 @
  const m = /@([\u4e00-\u9fa5\w]{0,20})$/.exec(t)
  if (!m) return null
  return { prefix: m[1], start: m.index }
}

function onInput(e) {
  const val = e.detail.value
  text.value = val
  if (!focused.value) return
  const hit = detectMention(val)
  if (hit && hit.prefix.length >= 0) {
    // @ 一触发就显示(空 prefix 也展示最近活跃用户?)— 这里要求至少输入 1 字
    if (hit.prefix.length === 0) {
      hideMention()
      return
    }
    showMention(hit.prefix, hit.start)
  } else {
    hideMention()
  }
}

function onFocus() {
  focused.value = true
}

function onBlur() {
  focused.value = false
  // 延迟隐藏,让 tap 事件先触发
  setTimeout(() => hideMention(), 200)
}

async function showMention(prefix, startIndex) {
  mentionPicker.visible = true
  mentionPicker.prefix = prefix
  mentionPicker.startIndex = startIndex
  emit('mention-shown', true)
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    mentionPicker.loading = true
    try {
      const list = await api.users.search(prefix)
      // 仅当仍是当前 prefix 时才更新(避免快速输入的竞态)
      if (mentionPicker.prefix === prefix) {
        mentionPicker.results = list || []
      }
    } catch {
      if (mentionPicker.prefix === prefix) mentionPicker.results = []
    } finally {
      if (mentionPicker.prefix === prefix) mentionPicker.loading = false
    }
  }, 200)
}

function hideMention() {
  mentionPicker.visible = false
  mentionPicker.results = []
  mentionPicker.prefix = ''
  mentionPicker.startIndex = -1
  emit('mention-shown', false)
}

function pickMention(user) {
  // 把 text 里的 @prefix 替换为 @nickname (加空格)
  const start = mentionPicker.startIndex
  if (start < 0) return
  const before = text.value.slice(0, start)
  const after = text.value.slice(start + 1 + mentionPicker.prefix.length) // 跳过 @和 prefix
  const insert = '@' + user.nickname + ' '
  text.value = before + insert + after
  // 记录 mention(发送时再按 @nickname 仍在文本中过滤)
  mentions.push({ id: user.id, nickname: user.nickname })
  hideMention()
}

// 父组件调用:进入回复模式
function setReply(target) {
  replyTarget.value = target
}

function cancelReply() {
  replyTarget.value = null
}

defineExpose({ setReply, cancelReply })

// ---------- 发送 ----------
async function onSend() {
  if (!canSend.value || sending.value) return
  // 校验最终保留的 mention id(@nickname 仍在文本中才算)
  const finalMentionIds = mentions
    .filter((m) => text.value.includes('@' + m.nickname))
    .map((m) => m.id)
  // 去重
  const uniqueIds = [...new Set(finalMentionIds)]

  sending.value = true
  try {
    const payload = {
      content: text.value.trim(),
      mentioned_user_ids: uniqueIds
    }
    if (replyTarget.value) {
      payload.parent_id = replyTarget.value.id
      // reply_to_user_id 默认指向被回复评论的作者(顶层评论作者)
      payload.reply_to_user_id =
        replyTarget.value.reply_to?.id || replyTarget.value.author?.id || null
    }
    const created = await api.comments.create(props.articleId, payload)
    emit('sent', created)
    // 清空
    text.value = ''
    mentions.length = 0
    replyTarget.value = null
    hideMention()
    uni.showToast({ title: '已发送', icon: 'none' })
  } catch {
    /* request 层已弹 toast */
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.cmt-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fdfbf7;
  border-top: 1rpx solid rgba(196, 168, 130, 0.18);
  padding: 16rpx 24rpx calc(env(safe-area-inset-bottom) + 16rpx);
  z-index: 200;
}
.reply-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 16rpx 12rpx;
}
.reply-text {
  font-size: 24rpx;
  color: #8d8d8d;
}
.cancel {
  font-size: 24rpx;
  color: #c4a882;
  padding: 4rpx 12rpx;
}
.bar {
  display: flex;
  align-items: flex-end;
  gap: 16rpx;
}
.input {
  flex: 1;
  min-height: 64rpx;
  max-height: 200rpx;
  padding: 16rpx 24rpx;
  background: #fff;
  border-radius: 32rpx;
  font-size: 28rpx;
  color: #4a4a4a;
  line-height: 1.5;
  box-shadow: 0 4rpx 16rpx rgba(196, 168, 130, 0.1);
}
.send-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 32rpx;
  background: #c4a882;
  color: #fff;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 500;
}
.send-btn.disabled {
  background: #d8cdb9;
  color: #f5efe5;
}
/* @提及浮层:位于输入框上方 */
.mention-pop {
  position: absolute;
  left: 24rpx;
  right: 24rpx;
  bottom: 100%;
  margin-bottom: 8rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
  max-height: 400rpx;
  overflow: hidden;
}
.mention-hint {
  padding: 16rpx 24rpx;
  font-size: 24rpx;
  color: #b0b0b0;
}
.mention-list {
  max-height: 400rpx;
}
.mention-item {
  display: flex;
  align-items: center;
  padding: 12rpx 24rpx;
}
.mention-item:active {
  background: #fdf6ec;
}
.m-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 24rpx;
}
.m-avatar.placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
}
.m-name {
  margin-left: 16rpx;
  font-size: 26rpx;
  color: #4a4a4a;
}
</style>
