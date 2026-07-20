<script>
import { isLoggedIn } from './store/user'

export default {
  onLaunch() {
    // 全局登录守卫:未登录直接进登录页
    if (!isLoggedIn()) {
      uni.reLaunch({ url: '/pages/login/index' })
    }
  }
}
</script>

<style>
/* 全局暖色基底 */
page {
  background-color: #FDFBF7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
    'Noto Sans', sans-serif;
  color: #4A4A4A;
  font-size: 30rpx;
  line-height: 1.8;
}

/* 色彩/圆角/阴影 —— CSS 变量,供各页面引用 */
page {
  --warm-white: #FDFBF7;
  --wood-bark: #C4A882;
  --moss-green: #88A07A;
  --sunset-pink: #E8C4C4;
  --text-main: #4A4A4A;
  --text-sec: #8D8D8D;
  --shadow-soft: 0 8rpx 64rpx rgba(196, 168, 130, 0.15);
  --radius-lg: 48rpx;
  --radius-md: 32rpx;
}

.status-bar-spacer {
  width: 100%;
}

/* 公共工具类 */
.container {
  padding: 0 48rpx;
}

.card {
  background: #fff;
  border-radius: 48rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: 0 8rpx 64rpx rgba(196, 168, 130, 0.15);
}

.tag {
  display: inline-block;
  padding: 6rpx 18rpx;
  background: rgba(136, 160, 122, 0.15);
  color: #88A07A;
  border-radius: 24rpx;
  font-size: 22rpx;
  margin-right: 12rpx;
}

.tag-pink {
  background: rgba(232, 196, 196, 0.25);
  color: #B88A8A;
}

.serif {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
}

* {
  -webkit-tap-highlight-color: transparent;
}

view,
text {
  -webkit-user-select: none;
  user-select: none;
}

input,
textarea {
  -webkit-user-select: text;
  user-select: text;
}
</style>
