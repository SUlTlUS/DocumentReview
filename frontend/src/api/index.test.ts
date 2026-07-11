import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { getErrorMessage } from './index'


describe('API timeout messaging', () => {
  it('turns Axios timeouts into an actionable message', () => {
    const error = new AxiosError('timeout of 240000ms exceeded', 'ECONNABORTED')

    expect(getErrorMessage(error)).toContain('稍后刷新页面查看结果')
    expect(getErrorMessage(error)).not.toContain('240000ms')
  })
})
