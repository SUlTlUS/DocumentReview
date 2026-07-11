import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusBadge from './StatusBadge.vue'

describe('StatusBadge', () => {
  it.each([
    ['ready', '就绪'],
    ['reviewing', '审核中'],
    ['parse_failed', '解析失败'],
  ])('renders %s with text as well as color', (status, label) => {
    const wrapper = mount(StatusBadge, { props: { status } })
    expect(wrapper.text()).toBe(label)
    expect(wrapper.classes()).toContain(`status-${status}`)
  })
})
