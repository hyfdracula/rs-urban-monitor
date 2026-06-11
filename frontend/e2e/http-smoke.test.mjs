import assert from 'node:assert/strict'
import test from 'node:test'

const FRONTEND_URL = process.env.E2E_FRONTEND_URL || 'http://127.0.0.1:5173'
const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://127.0.0.1:8001'
const GEOSERVER_URL = process.env.E2E_GEOSERVER_URL || 'http://127.0.0.1:8080/geoserver'
const REQUEST_TIMEOUT_MS = Number(process.env.E2E_REQUEST_TIMEOUT_MS || 10_000)

function joinUrl(base, path = '/') {
  return new URL(path, base.endsWith('/') ? base : `${base}/`).toString()
}

async function fetchWithTimeout(url) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    return await fetch(url, { signal: controller.signal })
  } catch (error) {
    throw new Error(`Request failed: ${url}\n${error.message}`)
  } finally {
    clearTimeout(timeout)
  }
}

async function expectOk(url) {
  const response = await fetchWithTimeout(url)
  assert.equal(response.ok, true, `${url} returned HTTP ${response.status}`)
  return response
}

test('frontend shell and key dev resources load', async () => {
  const response = await expectOk(joinUrl(FRONTEND_URL, '/'))
  const html = await response.text()

  assert.match(html, /<div id="app"><\/div>/)

  const moduleScripts = [...html.matchAll(/<script[^>]+type="module"[^>]+src="([^"]+)"/g)]
    .map(match => match[1])

  assert.ok(moduleScripts.length > 0, 'frontend index should include at least one module script')

  for (const scriptPath of moduleScripts) {
    const scriptResponse = await expectOk(joinUrl(FRONTEND_URL, scriptPath))
    assert.match(scriptResponse.headers.get('content-type') || '', /javascript|ecmascript/)
  }
})

test('backend system status is reachable directly', async () => {
  const response = await expectOk(joinUrl(BACKEND_URL, '/api/system/status'))
  const payload = await response.json()

  assert.equal(payload.status, 'ok')
  assert.equal(payload.services?.database, 'online')
  assert.equal(payload.services?.geoserver, 'online')
  assert.equal(payload.services?.gee, 'online')
})

test('frontend api proxy reaches backend system status', async () => {
  const response = await expectOk(joinUrl(FRONTEND_URL, '/api/system/status'))
  const payload = await response.json()

  assert.equal(payload.status, 'ok')
  assert.equal(payload.services?.database, 'online')
})

test('geoserver is reachable directly and through the frontend proxy', async () => {
  const direct = await expectOk(GEOSERVER_URL)
  assert.match(direct.headers.get('content-type') || '', /html|text|xml/)

  const proxied = await expectOk(joinUrl(FRONTEND_URL, '/geoserver'))
  assert.match(proxied.headers.get('content-type') || '', /html|text|xml/)
})
