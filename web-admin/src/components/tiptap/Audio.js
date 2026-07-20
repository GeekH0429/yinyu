// 自定义"音频"原子节点 —— TipTap 直接渲染真实 <audio controls>,可显示可播放
import { Node } from '@tiptap/core'

export const Audio = Node.create({
  name: 'audio',
  group: 'block',
  atom: true,
  selectable: true,
  draggable: true,

  addAttributes() {
    return {
      src: { default: null },
    }
  },

  parseHTML() {
    return [{ tag: 'audio[src]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'audio',
      {
        ...HTMLAttributes,
        controls: 'true',
        style: 'max-width:100%; width:100%;',
      },
    ]
  },

  addCommands() {
    return {
      setAudio:
        (options) =>
        ({ commands }) =>
          commands.insertContent([
            { type: 'audio', attrs: { src: options.src } },
            { type: 'paragraph' },
          ]),
    }
  },
})

export default Audio
