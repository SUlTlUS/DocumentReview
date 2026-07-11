import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ReviewResult from './ReviewResult.vue'
import { getDocument, getHealth, triggerReview } from '../api'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  RouterLink: { template: '<a><slot /></a>' },
}))
vi.mock('../api', () => ({
  getDocument: vi.fn(),
  getHealth: vi.fn(),
  getReviewResult: vi.fn(),
  triggerReview: vi.fn(),
  isNotFound: vi.fn(() => false),
  getErrorMessage: vi.fn(() => 'error'),
}))

describe('ReviewResult provider copy', () => {
  it('shows DeepSeek while a DeepSeek review is running', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok', llm_provider: 'deepseek', deepseek_api_configured: true, version: '2.0.0' })
    vi.mocked(getDocument).mockResolvedValue({
      id: 1, filename: 'contract.txt', file_type: 'txt', file_size: 10, status: 'ready',
      review_status: 'pending', upload_time: '', content_summary: '', chunk_count: 1,
      parse_method: 'digital', last_error: null,
    })
    vi.mocked(triggerReview).mockReturnValue(new Promise(() => {}))
    const wrapper = mount(ReviewResult, { global: { stubs: { KineticTitle: true } } })
    await flushPromises()
    await wrapper.get('button.button-primary').trigger('click')

    expect(wrapper.text()).toContain('DeepSeek 正在检查合规风险、条款缺失、模糊表述、权益不对等和数据合规。')
    expect(wrapper.text()).not.toContain('Mock 管线正在检查')
  })
})
