import { ElMessage } from 'element-plus'

/** 复制到剪贴板,带统一提示。 */
export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败')
  }
}
