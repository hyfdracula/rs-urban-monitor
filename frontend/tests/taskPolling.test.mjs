import assert from 'node:assert/strict'
import test from 'node:test'

import { useTaskPolling } from '../../src/composables/useTaskPolling.js'

test('polls task status and loads completed analysis once', async () => {
  const previousWindow = globalThis.window
  globalThis.window = {
    addEventListener() {},
    removeEventListener() {},
  }

  const notifications = []
  const completed = []
  const polling = useTaskPolling({
    getProgress: async () => ({ status: 'completed', progress: 100, current_step: '完成', current_year: 2020 }),
    getAnalysis: async taskId => ({ taskId, report: { ok: true } }),
    cancelTaskRequest: async () => ({}),
    isCurrent: token => token === 'token-1',
    onCompleted: async data => completed.push(data),
    notify: { success: message => notifications.push(message) },
  })

  polling.startProgressPolling('task-1', 'token-1')
  await new Promise(resolve => setTimeout(resolve, 0))
  polling.resetTaskPolling()
  globalThis.window = previousWindow

  assert.equal(polling.computing.value, false)
  assert.deepEqual(completed, [{ taskId: 'task-1', report: { ok: true } }])
  assert.deepEqual(notifications, ['计算完成！'])
  assert.deepEqual(polling.progressData.value, {
    percent: 100,
    step: '完成',
    year: 2020,
    taskId: 'task-1',
  })
})
