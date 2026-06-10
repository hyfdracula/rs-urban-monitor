import assert from 'node:assert/strict'
import test from 'node:test'

import { createBoundaryUploadForm, createUploadRequestConfig } from '../src/utils/uploadForm.js'

test('builds boundary upload form fields', async () => {
  const file = new File(['{}'], 'area.geojson', { type: 'application/geo+json' })

  const form = createBoundaryUploadForm(
    file,
    '测试区域',
    [2010, 2020],
    'online',
    { indicators: ['rsei'] },
  )

  assert.equal(form.get('file'), file)
  assert.equal(form.get('name'), '测试区域')
  assert.equal(form.get('years'), '[2010,2020]')
  assert.equal(form.get('compute_mode'), 'online')
  assert.equal(form.get('config'), '{"indicators":["rsei"]}')
})

test('lets the browser set multipart content-type boundary', () => {
  const config = createUploadRequestConfig(() => {}, 120000)

  assert.equal(Object.hasOwn(config, 'headers'), false)
  assert.equal(typeof config.onUploadProgress, 'function')
  assert.equal(config.timeout, 120000)
})
