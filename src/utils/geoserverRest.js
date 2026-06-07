import axios from 'axios'
import { GEOSERVER_CONFIG } from '../config/map'

const REST_BASE = `${GEOSERVER_CONFIG.baseUrl}/rest`

// GeoServer default credentials (standard dev setup)
const AUTH = {
  username: 'admin',
  password: 'geoserver',
}

const restClient = axios.create({
  baseURL: REST_BASE,
  timeout: 60000,
  auth: AUTH,
  headers: { 'Content-Type': 'application/json' },
})

// =============================================================
// Workspace operations
// =============================================================

/**
 * List all workspaces
 */
export async function listWorkspaces() {
  const resp = await restClient.get('/workspaces.json')
  return resp.data.workspaces?.workspace || []
}

/**
 * Get or create a workspace
 */
export async function ensureWorkspace(name) {
  const ws = await listWorkspaces()
  const found = ws.find(w => w.name === name)
  if (found) return found

  const resp = await restClient.post('/workspaces.json', { workspace: { name } })
  // 201 created
  return { name }
}

// =============================================================
// Layer listing
// =============================================================

/**
 * List all layers in a workspace
 */
export async function listLayers(workspace) {
  const resp = await restClient.get(`/workspaces/${workspace}/layers.json`)
  return resp.data.layers?.layer || []
}

/**
 * Check if a layer exists
 */
export async function layerExists(workspace, layerName) {
  const layers = await listLayers(workspace)
  return layers.some(l => l.name === layerName)
}

// =============================================================
// Publish GeoJSON → GeoServer (vector data store)
// =============================================================

/**
 * Publish a GeoJSON object as a WMS layer
 * Creates a data store + feature type automatically
 */
export async function publishGeoJSON(workspace, layerName, geojson, options = {}) {
  await ensureWorkspace(workspace)

  const dataStoreName = `${layerName}_store`

  // Step 1: Check if datastore exists; if not create it
  const dsExists = await checkDataStoreExists(workspace, dataStoreName)

  if (!dsExists) {
    // Create the datastore pointing to GeoJSON via external upload
    await restClient.post(
      `/workspaces/${workspace}/datastores.json`,
      {
        dataStore: {
          name: dataStoreName,
          type: 'GeoJSON',
          connectionParameters: {
            entry: [{ '@key': 'geometry_type', $: 'Geometry' }],
          },
        },
      },
      { headers: { 'Content-Type': 'application/json' } }
    )

    // Upload the GeoJSON file to the datastore
    const geojsonStr = JSON.stringify(geojson)
    await restClient.put(
      `/workspaces/${workspace}/datastores/${dataStoreName}/file.geojson`,
      geojsonStr,
      { headers: { 'Content-Type': 'application/geo+json' } }
    )
  }

  // Step 2: Check if feature type exists, if not create it
  const ftExists = await checkFeatureTypeExists(workspace, dataStoreName, layerName)

  if (!ftExists) {
    await restClient.post(
      `/workspaces/${workspace}/datastores/${dataStoreName}/featuretypes.json`,
      {
        featureType: {
          name: layerName,
          title: options.title || layerName,
          srs: 'EPSG:4326',
          enabled: true,
        },
      }
    )
  } else {
    // Update the feature type
    await restClient.put(
      `/workspaces/${workspace}/datastores/${dataStoreName}/featuretypes/${layerName}.json`,
      {
        featureType: {
          name: layerName,
          title: options.title || layerName,
          enabled: true,
        },
      }
    )
  }

  return {
    workspace,
    layerName,
    wmsUrl: `${GEOSERVER_CONFIG.wmsUrl}?service=WMS&version=1.1.1&request=GetMap&layers=${workspace}:${layerName}&srs=EPSG:4326&width=800&height=600&format=image/png&bbox=-180,-90,180,90`,
    wfsUrl: `${GEOSERVER_CONFIG.baseUrl}/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=${workspace}:${layerName}&outputFormat=application/json`,
  }
}

// =============================================================
// Publish Style (SLD)
// =============================================================

/**
 * Apply a default style to a layer based on type
 */
export async function applyStyle(workspace, layerName, styleType) {
  const styleName = `${layerName}_style`
  const sld = buildSLD(styleType, layerName)

  // Create style
  await restClient.post(
    '/styles.json',
    {
      style: {
        name: styleName,
        filename: `${styleName}.sld`,
      },
    }
  )

  // Upload SLD body
  await restClient.put(
    `/styles/${styleName}`,
    sld,
    { headers: { 'Content-Type': 'application/vnd.ogc.sld+xml' } }
  )

  // Apply to layer
  await restClient.put(
    `/layers/${workspace}:${layerName}.json`,
    {
      layer: {
        defaultStyle: { name: styleName },
      },
    }
  )

  return { styleName }
}

// =============================================================
// Delete
// =============================================================

/**
 * Delete a layer and its store
 */
export async function deleteLayer(workspace, layerName) {
  const dataStoreName = `${layerName}_store`

  try {
    await restClient.delete(
      `/workspaces/${workspace}/datastores/${dataStoreName}/featuretypes/${layerName}.json?recurse=true`
    )
  } catch (e) {
    // layer may not exist
  }

  try {
    await restClient.delete(
      `/workspaces/${workspace}/datastores/${dataStoreName}.json?recurse=true`
    )
  } catch (e) {
    // store may not exist
  }
}

// =============================================================
// Helpers
// =============================================================

async function checkDataStoreExists(workspace, storeName) {
  try {
    await restClient.get(`/workspaces/${workspace}/datastores/${storeName}.json`)
    return true
  } catch {
    return false
  }
}

async function checkFeatureTypeExists(workspace, storeName, ftName) {
  try {
    await restClient.get(
      `/workspaces/${workspace}/datastores/${storeName}/featuretypes/${ftName}.json`
    )
    return true
  } catch {
    return false
  }
}

/**
 * Build a simple SLD for styling
 */
function buildSLD(styleType, layerName) {
  const palettes = {
    construction: { color: '#FF6B6B', name: '建设用地分布' },
    expansion: { color: '#FFA94D', name: '新增建设用地' },
    rsei: { color: '#51CF66', name: '遥感生态指数' },
    hotspot: { color: '#ff4444', name: '热点分析' },
  }

  const palette = palettes[styleType] || palettes.construction

  return `<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>${layerName}</Name>
    <UserStyle>
      <Title>${palette.name}</Title>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">${palette.color}</CssParameter>
              <CssParameter name="fill-opacity">0.6</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">${palette.color}</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>`
}

// =============================================================
// Publishable layers from analysis result types
// =============================================================

/**
 * Get the list of publishable analysis layers
 */
export function getPublishableLayers() {
  return [
    {
      id: 'construction-land',
      name: '建设用地分布图',
      category: '建设扩张',
      styleType: 'construction',
      description: '多期建设用地空间分布，可对比查看城市扩张过程',
    },
    {
      id: 'expansion-mode',
      name: '扩张模式分布图',
      category: '建设扩张',
      styleType: 'expansion',
      description: '边缘扩张、填充式扩张、飞地式扩张的空间分布',
    },
    {
      id: 'rsei-grade',
      name: '生态质量等级图',
      category: '生态环境',
      styleType: 'rsei',
      description: '基于RSEI的五个生态质量等级空间分布',
    },
    {
      id: 'rsei-change',
      name: '生态变化检测图',
      category: '生态环境',
      styleType: 'rsei',
      description: '两期RSEI变化分类：改善/不变/退化',
    },
    {
      id: 'hotspot',
      name: '扩张热点乡镇图',
      category: '建设扩张',
      styleType: 'hotspot',
      description: '基于空间统计的建设用地扩张热点和冷点乡镇',
    },
  ]
}

export default restClient
