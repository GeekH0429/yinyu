// 自定义"视频"原子节点
import { Node } from '@tiptap/core'

export const Video = Node.create({
  name: 'video',
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
    return [{ tag: 'video[src]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      { style: 'text-align:center; margin:8px 0;' },
      [
        'video',
        {
          ...HTMLAttributes,
          controls: 'true',
          style: 'max-width:100%;',
        },
      ],
    ]
  },

  addCommands() {
    return {
      setVideo:
        (options) =>
        ({ commands }) =>
          commands.insertContent([
            { type: 'video', attrs: { src: options.src } },
            { type: 'paragraph' },
          ]),
    }
  },
})

export default Video
