<template>
  <view class="cmt">
    <view class="row">
      <CachedImage
        v-if="comment.author && comment.author.avatar_url"
        class="avatar"
        :src="comment.author.avatar_url"
        mode="aspectFill"
      />
      <view v-else class="avatar placeholder">
        {{ (comment.author?.nickname || '?').slice(0, 1) }}
      </view>
      <view class="main">
        <view class="meta">
          <text class="name">{{ comment.author?.nickname || '佚名' }}</text>
          <text v-if="isArticleAuthor" class="author-chip">作者</text>
          <text v-if="comment.reply_to" class="reply-prefix">
            回复 @{{ comment.reply_to.nickname }}
          </text>
        </view>
        <text class="time">{{ formatRelative(comment.created_at) }}</text>
      </view>
      <view v-if="canDelete" class="del" @tap="onDelete">删除</view>
    </view>
    <text class="content">{{ comment.content }}</text>
    <view class="footer">
      <text class="action reply" @tap="onReply">回复</text>
      <view :class="['action', 'like', { liked: comment.liked_by_me }]" @tap="onLike">
        <text :class="['heart', { pop: pulse }]">{{ comment.liked_by_me ? '♥' : '♡' }}</text>
        <text class="like-num">{{ comment.like_count || '' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { api } from '../api'
import { formatRelative } from '../utils/format'
import CachedImage from './CachedImage.vue'

const props = defineProps({
  comment: { type: Object, required: true },
  articleAuthorId: { type: Number, default: null },
  currentUserId: { type: Number, default: null },
  isAdmin: { type: Boolean, default: false }
})

const emit = defineEmits(['reply', 'deleted', 'like-toggled'])

const pulse = ref(false)
const isArticleAuthor = computed(
  () => props.articleAuthorId != null && props.comment.author?.id === props.articleAuthorId
)
const canDelete = computed(
  () =>
    (props.currentUserId != null && props.comment.author?.id === props.currentUserId) ||
    props.isAdmin
)

function onReply() {
  emit('reply', props.comment)
}

async function onLike() {
  try {
    const res = await api.comments.like(props.comment.id)
    // 直接改 prop 对象(父组件传入的是响应式 items 中的元素)
    props.comment.liked_by_me = res.liked
    props.comment.like_count = (props.comment.like_count || 0) + (res.liked ? 1 : -1)
    if (res.liked) {
      pulse.value = false
      nextTick(() => {
        pulse.value = true
      })
    }
    emit('like-toggled', props.comment)
  } catch {
    /* ignore */
  }
}

async function onDelete() {
  uni.showModal({
    title: '删除评论',
    content: '确定要删除这条评论吗?',
    confirmColor: '#e0a8b0',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.comments.remove(props.comment.id)
        uni.showToast({ title: '已删除', icon: 'none' })
        emit('deleted', props.comment)
      } catch {
        /* ignore */
      }
    }
  })
}
</script>

<style scoped>
.cmt {
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.12);
}
.row {
  display: flex;
  align-items: flex-start;
}
.avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  flex-shrink: 0;
}
.avatar.placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}
.main {
  flex: 1;
  margin-left: 16rpx;
  min-width: 0;
}
.meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8rpx;
}
.name {
  font-size: 26rpx;
  color: #4a4a4a;
  font-weight: 500;
}
.author-chip {
  font-size: 20rpx;
  color: #c4a882;
  border: 1rpx solid #c4a882;
  border-radius: 6rpx;
  padding: 0 8rpx;
  line-height: 1.5;
}
.reply-prefix {
  font-size: 24rpx;
  color: #8d8d8d;
}
.time {
  display: block;
  font-size: 22rpx;
  color: #b0b0b0;
  margin-top: 4rpx;
}
.del {
  font-size: 22rpx;
  color: #b0b0b0;
  padding: 4rpx 8rpx;
}
.content {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
  color: #4a4a4a;
  line-height: 1.6;
  word-break: break-word;
}
.footer {
  display: flex;
  gap: 32rpx;
  margin-top: 12rpx;
}
.action {
  font-size: 24rpx;
  color: #8d8d8d;
  display: flex;
  align-items: center;
  gap: 6rpx;
}
.action.reply {
  padding: 4rpx 0;
}
.action.like.liked {
  color: #e0a8b0;
}
.heart {
  font-size: 28rpx;
  display: inline-block;
}
.heart.pop {
  animation: heartPop 0.45s ease;
}
@keyframes heartPop {
  0% { transform: scale(1); }
  40% { transform: scale(1.45); }
  70% { transform: scale(0.88); }
  100% { transform: scale(1); }
}
.like-num {
  min-width: 24rpx;
  text-align: center;
}
</style>
