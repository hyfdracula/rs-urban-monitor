import { ref } from 'vue'

export function useTaskPolling({
  getProgress,
  getAnalysis,
  cancelTaskRequest,
  isCurrent = () => true,
  onCompleted,
  notify = {},
}) {
  const computing = ref(false)
  const progressData = ref({ percent: 0, step: '', year: null, taskId: null })
  let progressTimer = null
  let beforeUnloadHandler = null

  function installBeforeUnload() {
    if (beforeUnloadHandler) return
    beforeUnloadHandler = (event) => {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', beforeUnloadHandler)
  }

  function uninstallBeforeUnload() {
    if (!beforeUnloadHandler) return
    window.removeEventListener('beforeunload', beforeUnloadHandler)
    beforeUnloadHandler = null
  }

  function stopProgressPolling() {
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
  }

  function resetTaskPolling() {
    computing.value = false
    stopProgressPolling()
    uninstallBeforeUnload()
  }

  function startProgressPolling(taskId, token) {
    stopProgressPolling()
    computing.value = true
    installBeforeUnload()

    async function poll() {
      try {
        const data = await getProgress(taskId)
        progressData.value = {
          percent: data.progress || 0,
          step: data.current_step || '',
          year: data.current_year,
          taskId,
        }

        if (data.status === 'completed') {
          resetTaskPolling()
          const full = await getAnalysis(taskId)
          if (!isCurrent(token)) return
          await onCompleted(full, token, taskId)
          notify.success?.('计算完成！')
          return
        }

        if (data.status === 'failed') {
          resetTaskPolling()
          notify.error?.('计算失败')
          return
        }

        if (data.status === 'cancelled') {
          resetTaskPolling()
          notify.info?.('已取消')
        }
      } catch {
        // Keep polling; transient network/backend restarts are expected during long tasks.
      }
    }

    poll()
    progressTimer = setInterval(poll, 3000)
  }

  async function cancelTask() {
    try {
      await cancelTaskRequest(progressData.value.taskId)
      notify.info?.('已发送取消请求')
    } catch {
      notify.error?.('取消失败')
    }
  }

  return {
    computing,
    progressData,
    startProgressPolling,
    stopProgressPolling,
    resetTaskPolling,
    cancelTask,
  }
}
