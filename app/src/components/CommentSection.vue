<template>
  <view class="cmt-section">
    <view class="cmt-header">
      <text class="cmt-title">评论</text>
      <text class="cmt-count">{{ topLevelCount }}</text>
    </view>

    <StateView
      v-if="!loading && !items.length && !loadError"
      type="empty"
      text="还没有评论,留下第一句温柔吧"
    />
    <StateView
      v-else-if="loadError && !items.length"
      type="error"
      text="评论加载失败"
      retry
      @retry="reload"
    />

    <!-- 顶层评论 + 各自回复 -->
    <view class="cmt-list">
      <template v-for="group in grouped" :key="group.top.id">
        <CommentItem
          :comment="group.top"
          :article-author-id="articleAuthorId"
          :current-user-id="currentUserId"
          :is-admin="isAdmin"
          @reply="onReply"
          @deleted="onDeleted"
        />
        <view v-if="group.replies.length" class="replies">
          <CommentItem
            v-for="r in group.replies"
            :key="r.id"
            :comment="r"
            :article-author-id="articleAuthorId"
            :current-user-id="currentUserId"
            :is-admin="isAdmin"
            @reply="onReply"
            @deleted="onDeleted"
          />
        </view>
      </template>
    </view>

    <view v-if="items.length" class="load-more" @tap="loadMore">
      <text v-if="loadingMore">加载中…</text>
      <text v-else-if="hasMore">加载更多</text>
      <text v-else class="end">没有更多了</text>
    </view>

    <!-- 底部输入条(固定) -->
    <CommentBar
      ref="barRef"
      :article-id="articleId"
      @sent="onSent"
    />

    <!-- 占位:防止固定输入条遮挡内容 -->
    <view class="bar-placeholder"></view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '../api'
import { getUser } from '../store/user'
import CommentItem from './CommentItem.vue'
import CommentBar from './CommentBar.vue'
import StateView from './StateView.vue'

const props = defineProps({
  articleId: { type: Number, required: true },
  articleAuthorId: { type: Number, default: null },
  articleCommentCount: { type: Number, default: 0 }
})

const items = ref([]) // 扁平列表
const loading = ref(false)
const loadingMore = ref(false)
const loadError = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

const barRef = ref(null)

const currentUser = getUser()
const currentUserId = currentUser?.id ?? null
const isAdmin = currentUser?.role === 'admin'

const hasMore = computed(() => page.value * pageSize < total.value)
// 顶层评论数 = 实际顶层(parent_id 为 null)的数量;total 是后端返回的顶层评论计数
const topLevelCount = computed(() => {
  const tl = items.value.filter((c) => !c.parent_id).length
  return tl > 0 ? tl : (total.value || props.articleCommentCount || 0)
})

// 按 parent_id 分组:顶层在前,回复挂在其父下
const grouped = computed(() => {
  const map = new Map()
  const result = []
  // 先扫一遍建立 parent -> replies
  for (const c of items.value) {
    if (c.parent_id) {
      if (!map.has(c.parent_id)) map.set(c.parent_id, [])
      map.get(c.parent_id).push(c)
    }
  }
  // 再扫一遍顶层,按出现顺序组装
  for (const c of items.value) {
    if (!c.parent_id) {
      result.push({ top: c, replies: map.get(c.id) || [] })
    }
  }
  return result
})

async function load(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
  }
  loading.value = reset
  loadError.value = false
  try {
    const res = await api.comments.list(props.articleId, {
      page: page.value,
      page_size: pageSize
    })
    if (reset) {
      items.value = res.items
    } else {
      items.value = items.value.concat(res.items)
    }
    total.value = res.total || 0
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  try {
    const res = await api.comments.list(props.articleId, {
      page: page.value,
      page_size: pageSize
    })
    items.value = items.value.concat(res.items)
    total.value = res.total || 0
  } catch {
    page.value-- // 回滚页码,允许重试
  } finally {
    loadingMore.value = false
  }
}

function reload() {
  load(true)
}

function onReply(comment) {
  // 只能回复顶层评论(单层回复约束)
  const target = comment.parent_id
    ? items.value.find((c) => c.id === comment.parent_id) || comment
    : comment
  barRef.value?.setReply(target)
}

function onDeleted(comment) {
  // 移除该评论;若为顶层,一并移除其所有回复
  items.value = items.value.filter((c) => {
    if (c.id === comment.id) return false
    if (comment.parent_id == null && c.parent_id === comment.id) return false
    return true
  })
  // total 是顶层计数:仅顶层删除时 -1
  if (!comment.parent_id && total.value > 0) total.value--
}

function onSent(created) {
  // 追加到列表;若是回复,插入到对应父组末尾;若是顶层,追加到末尾
  if (created.parent_id) {
    items.value.push(created)
  } else {
    items.value.push(created)
    total.value++
  }
}

onMounted(() => load(true))
</script>

<style scoped>
.cmt-section {
  margin-top: 56rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(196, 168, 130, 0.15);
}
.cmt-header {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-bottom: 8rpx;
}
.cmt-title {
  font-size: 30rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.cmt-count {
  font-size: 24rpx;
  color: #b0b0b0;
}
.cmt-list {
  /* 内边距:左侧 0(顶层与标题对齐),右侧 0 */
}
.replies {
  margin-left: 40rpx;
  padding-left: 24rpx;
  border-left: 2rpx solid rgba(196, 168, 130, 0.18);
}
.load-more {
  text-align: center;
  padding: 24rpx 0;
  font-size: 24rpx;
  color: #c4a882;
}
.load-more .end {
  color: #c8c8c8;
}
.bar-placeholder {
  /* 输入条高度 + 安全区:防止内容被遮挡 */
  height: 160rpx;
}
</style>
