import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'
import { getHealth } from './api'

vi.mock('./api', () => ({ getHealth: vi.fn() }))
const mockedHealth = vi.mocked(getHealth)
const stubs = { RouterLink: { template: '<a><slot /></a>' }, RouterView: { template: '<div />' }, Transition: false }

describe('App environment status', () => {
  beforeEach(() => mockedHealth.mockReset())

  it('shows configured DeepSeek status without exposing the key', async () => {
    mockedHealth.mockResolvedValue({ status: 'ok', llm_provider: 'deepseek', deepseek_api_configured: true, version: '2.0.0' })
    const wrapper = mount(App, { global: { stubs } })
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toContain('DeepSeek API 已配置')
  })

  it('warns when DeepSeek is selected without an API key', async () => {
    mockedHealth.mockResolvedValue({ status: 'ok', llm_provider: 'deepseek', deepseek_api_configured: false, version: '2.0.0' })
    const wrapper = mount(App, { global: { stubs } })
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toContain('DeepSeek API 未配置')
    expect(wrapper.get('.status-dot').classes()).toContain('status-dot--warning')
  })
})
