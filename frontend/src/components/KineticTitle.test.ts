import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import KineticTitle from './KineticTitle.vue'

describe('KineticTitle', () => {
  it('keeps an accessible static title while characters animate visually', () => {
    const wrapper = mount(KineticTitle, {
      props: { eyebrow: 'Review', title: '审核结果', description: '风险说明' },
    })

    expect(wrapper.get('h1').attributes('aria-label')).toBe('审核结果')
    expect(wrapper.findAll('.kinetic-character')).toHaveLength(4)
    expect(wrapper.text()).toContain('风险说明')
  })
})
