<template>
  <MapLayout :tabs="tabs" default-tab="overview" :show-layer-control="true" :show-legend="false">
    <template #map>
      <MapViewer ref="mapRef" @map-loaded="onMapLoaded" />
      <CustomLegendBar :map-layers="mapLayers" :visible-types="visibleTypes" />
      <BottomBar v-if="report" :items="customBottomItems" @item-click="onBottomBarClick" />
    </template>

    <template #layer-control>
      <CustomLayerControl
        :map-layers="mapLayers"
        :visible-types="visibleTypes"
        @layer-toggle="onLayerToggle"
      />
    </template>

    <!-- 总览: 研究区信息 + 核心结论 + 指标 -->
    <template #overview>
      <!-- 计算进度 -->
      <div v-if="computing" class="progress-overlay">
        <h4>计算进度</h4>
        <el-progress :percentage="progressData.percent" :status="progressStatus" :stroke-width="10" />
        <p class="progress-step">{{ progressData.step || '准备中...' }}</p>
        <p class="progress-warn">⚠️ 计算正在进行，请勿离开页面</p>
        <el-button type="danger" size="small" plain @click="cancelTask">取消计算</el-button>
      </div>

      <div v-if="report && !computing" class="overview-section">
        <!-- 研究区信息头 -->
        <div class="report-header">
          <div class="header-row">
            <span class="header-title">{{ overview.studyArea || '自定义研究区' }}</span>
            <span class="rsei-badge" :class="overview.rseiGrade">{{ overview.rseiGradeLabel || '—' }}</span>
          </div>
          <div class="header-meta">
            <span v-if="overview.yearRange" class="meta-tag">📅 {{ overview.yearRange }}</span>
            <span v-if="overview.totalBuiltArea" class="meta-tag">🏗️ 建设用地 {{ fmt(overview.totalBuiltArea) }} km²</span>
            <span v-if="overview.gdp" class="meta-tag">💰 GDP {{ overview.gdp }} 亿元</span>
          </div>
        </div>

        <!-- 核心结论 -->
        <div class="conclusion-box" v-if="overview.conclusion">
          <div class="conclusion-label">核心结论</div>
          <p class="conclusion-text">{{ overview.conclusion }}</p>
        </div>

        <!-- 2×4 指标网格 -->
        <div class="overview-grid">
          <div class="ind-card">
            <span class="ind-label">研究区域</span>
            <span class="ind-value ind-name">{{ overview.studyArea || '—' }}</span>
          </div>
          <div class="ind-card">
            <div class="ind-head"><span class="ind-label">新增建设用地</span><MockBadge v-if="overview.mock?.newConstruction" /></div>
            <span class="ind-value">{{ fmt(overview.newConstruction) }} <span class="ind-unit">km²</span></span>
          </div>
          <div class="ind-card">
            <div class="ind-head"><span class="ind-label">年均扩张速率</span><MockBadge v-if="overview.mock?.expansionRate" /></div>
            <span class="ind-value">{{ fmt(overview.expansionRate) }} <span class="ind-unit">%</span></span>
          </div>
          <div class="ind-card">
            <span class="ind-label">RSEI 均值</span>
            <span class="ind-value">{{ fmt(overview.rseiMean, 3) }}</span>
          </div>
          <div class="ind-card">
            <div class="ind-head"><span class="ind-label">生态改善面积</span><MockBadge v-if="overview.mock?.improvedArea" /></div>
            <span class="ind-value eco-good">{{ fmt(overview.improvedArea) }} <span class="ind-unit">km²</span></span>
          </div>
          <div class="ind-card">
            <div class="ind-head"><span class="ind-label">生态退化面积</span><MockBadge v-if="overview.mock?.degradedArea" /></div>
            <span class="ind-value eco-bad">{{ fmt(overview.degradedArea) }} <span class="ind-unit">km²</span></span>
          </div>
          <div class="ind-card">
            <span class="ind-label">常住人口</span>
            <span class="ind-value">{{ fmt(overview.population) }} <span class="ind-unit">万</span></span>
          </div>
          <div class="ind-card">
            <span class="ind-label">GDP（亿人民币）</span>
            <span class="ind-value">{{ overview.gdp || '—' }}</span>
          </div>
        </div>

        <!-- 数据来源 -->
        <div class="data-sources" v-if="overview.dataSources?.length">
          <span class="src-label">数据来源：</span>
          <span class="src-tag" v-for="src in overview.dataSources" :key="src">{{ src }}</span>
        </div>

        <el-alert v-if="overview.singleYearNote" type="info" :closable="false" style="margin-top:8px">{{ overview.singleYearNote }}</el-alert>
      </div>
    </template>

    <!-- 生态评估 -->
    <template #ecology>
      <div class="panel-content" v-if="!report"><p class="hint">请先选择研究区</p></div>
      <div class="panel-content" v-else>
        <h3 class="panel-title">生态评估</h3>

        <!-- RSEI 均值 + 等级 + 变化方向 -->
        <div class="stat-cards">
          <div class="stat-card">
            <div class="stat-head-row"><span class="stat-lbl">RSEI 均值</span></div>
            <div class="stat-val">{{ fmt(report.ecology?.rseiMean, 3) }}</div>
            <div class="stat-grade" v-if="report.ecology?.rseiGradeLabel">
              <span class="grade-badge" :class="report.ecology?.rseiGrade">{{ report.ecology.rseiGradeLabel }}</span>
              <span class="grade-hint">生态等级</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-head-row">
              <span class="stat-lbl">RSEI 变化</span>
              <MockBadge v-if="!report.ecology?.rseiChange && report.ecology?.rseiChange !== 0" />
            </div>
            <div class="stat-val" :style="{ color: rseiChangeColor }">{{ fmt(report.ecology?.rseiChange, 3) }}</div>
            <div class="stat-dir" v-if="report.ecology?.changeDirection" :class="{ 'dir-good': report.ecology.changeDirection.includes('改善'), 'dir-bad': report.ecology.changeDirection.includes('退化') }">
              {{ report.ecology.changeDirection }}
            </div>
          </div>
        </div>

        <!-- 面板描述 -->
        <div class="panel-desc" v-if="report.ecology?.description">
          <p>{{ report.ecology.description }}</p>
        </div>

        <div class="chart-section"><h4 class="sec-title">生态等级分布</h4><div ref="gradeChartRef" class="chart-box" /></div>
        <div class="chart-section"><h4 class="sec-title">RSEI 时序变化</h4><div ref="trendChartRef" class="chart-box" /></div>
        <div class="chart-section" v-if="report.ecology?.changeDistribution?.length"><h4 class="sec-title">生态变化面积</h4><div ref="changeChartRef" class="chart-box" /></div>
        <div class="chart-section"><h4 class="sec-title">RSEI 四维指标</h4><div ref="radarChartRef" class="chart-box tall" /></div>
      </div>
    </template>

    <!-- 建设用地 -->
    <template #construction>
      <div class="panel-content" v-if="!report"><p class="hint">请先选择研究区</p></div>
      <div class="panel-content" v-else>
        <h3 class="panel-title">建设用地</h3>
        <div class="stat-cards">
          <div class="stat-card">
            <div class="stat-lbl">总面积</div>
            <div class="stat-val">{{ fmt(report.expansion?.totalArea) }} <span class="stat-unit">km²</span></div>
            <div class="stat-note" v-if="report.expansion?.totalAreaDesc">{{ report.expansion.totalAreaDesc }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-head-row"><span class="stat-lbl">新增面积</span><MockBadge v-if="report.expansion?.mock?.newArea" /></div>
            <div class="stat-val">{{ fmt(report.expansion?.newArea) }} <span class="stat-unit">km²</span></div>
            <div class="stat-note" v-if="report.expansion?.newAreaDesc">{{ report.expansion.newAreaDesc }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-head-row"><span class="stat-lbl">斑块数</span></div>
            <div class="stat-val">{{ report.expansion?.patches || '—' }}</div>
            <div class="stat-note">面积÷平均斑块尺度（0.5 km²）</div>
          </div>
          <div class="stat-card">
            <div class="stat-head-row"><span class="stat-lbl">年均扩张速率</span><MockBadge v-if="report.expansion?.mock?.expansionRate" /></div>
            <div class="stat-val">{{ fmt(report.expansion?.expansionRate) }} <span class="stat-unit">%</span></div>
            <div class="stat-note" v-if="report.expansion?.expansionRateDesc">{{ report.expansion.expansionRateDesc }}</div>
          </div>
        </div>

        <!-- 面板描述 -->
        <div class="panel-desc" v-if="report.expansion?.description">
          <p>{{ report.expansion.description }}</p>
        </div>

        <el-alert v-if="report.expansion?.singleYearNote" type="info" :closable="false" style="margin-top:8px">{{ report.expansion.singleYearNote }}</el-alert>
        <div class="chart-section" v-if="report.expansion?.districtRanking?.length">
          <h4 class="sec-title">区县扩张排名</h4>
          <div ref="expBarChartRef" class="chart-box" />
        </div>
      </div>
    </template>

    <!-- 社会经济 -->
    <template #socio>
      <div class="panel-content" v-if="!report"><p class="hint">请先选择研究区</p></div>
      <div class="panel-content" v-else>
        <h3 class="panel-title">社会经济</h3>

        <!-- 人口 -->
        <div class="sub-section">
          <h4 class="sub-title">人口</h4>
          <div class="stat-cards">
            <div class="stat-card">
              <div class="stat-val">{{ report.socio?.population?.total || '—' }}</div>
              <div class="stat-lbl">常住人口 <span class="unit-hint">(万人)</span></div>
            </div>
            <div class="stat-card">
              <div class="stat-head-row"><span class="stat-lbl">人口增长率</span></div>
              <div class="stat-val">{{ fmt(report.socio?.population?.growth) }} <span class="stat-unit">%</span></div>
              <div class="stat-note" v-if="report.socio?.population?.growthDesc">{{ report.socio.population.growthDesc }}</div>
            </div>
          </div>
        </div>

        <!-- GDP -->
        <div class="sub-section">
          <h4 class="sub-title">GDP</h4>
          <div class="stat-cards">
            <div class="stat-card">
              <div class="stat-val">{{ report.socio?.gdp?.total || '—' }}</div>
              <div class="stat-lbl">GDP 总量 <span class="unit-hint">(亿人民币)</span></div>
            </div>
            <div class="stat-card">
              <div class="stat-val">{{ report.socio?.gdp?.perCapita || '—' }}</div>
              <div class="stat-lbl">人均 GDP <span class="unit-hint">(万元)</span></div>
            </div>
          </div>
          <div class="stat-cards" style="margin-top:8px">
            <div class="stat-card">
              <div class="stat-head-row"><span class="stat-lbl">总GDP增量</span></div>
              <div class="stat-val">{{ fmt(report.socio?.gdp?.increment) }} <span class="stat-unit">亿人民币</span></div>
              <div class="stat-note" v-if="report.socio?.gdp?.incrementDesc">{{ report.socio.gdp.incrementDesc }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-head-row"><span class="stat-lbl">GDP年增速</span></div>
              <div class="stat-val">{{ fmt(report.socio?.gdp?.growth) }} <span class="stat-unit">%</span></div>
              <div class="stat-note" v-if="report.socio?.gdp?.growthDesc">{{ report.socio.gdp.growthDesc }}</div>
            </div>
          </div>
        </div>

        <!-- 面板描述 -->
        <div class="panel-desc" v-if="report.socio?.description">
          <p>{{ report.socio.description }}</p>
        </div>

        <div class="chart-section" v-if="report.socio?.industryStructure?.length">
          <h4 class="sec-title">产业结构</h4>
          <div ref="industryPieRef" class="chart-box" />
        </div>
        <div class="chart-section" v-if="report.socio?.districtPopulation?.length">
          <h4 class="sec-title">区县人口排名 <span class="unit-hint">(人)</span></h4>
          <div ref="popBarRef" class="chart-box" />
        </div>
        <div class="chart-section" v-if="report.socio?.districtGdp?.length">
          <h4 class="sec-title">区县 GDP 排名 <span class="unit-hint">(亿人民币)</span></h4>
          <div ref="gdpBarRef" class="chart-box" />
        </div>
      </div>
    </template>

    <!-- 分析任务 -->
    <template #tasks>
      <CustomAreaPanel ref="panelRef" @select="onTaskSelect" @deselect="onTaskDeselect" />
    </template>

    <!-- 占位 -->
    <template #placeholder>
      <div class="panel-content"><p class="hint">敬请期待</p></div>
    </template>

    <!-- 分析报告 -->
    <template #report>
      <div class="panel-content" v-if="!report"><p class="hint">请先选择研究区</p></div>
      <div class="panel-content" v-else>
        <!-- 🏙️ 卡片 -->
        <div class="dl-card" @click="showReportDialog = true">
          <span class="dl-icon">🏙️</span>
          <div class="dl-info">
            <span class="dl-name">分析报告</span>
            <span class="dl-desc">PDF 格式完整监测报告</span>
          </div>
          <span class="dl-arrow">›</span>
        </div>

        <!-- ====== 报告正文 ====== -->
        <div class="rpt-body">
          <!-- 1. 综合结论 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">1</span>综合结论</h4>
            <p class="rpt-p">{{ report.overview?.conclusion || '暂无结论数据。' }}</p>
            <div class="rpt-kpi-row">
              <div v-if="report.overview?.totalBuiltArea != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.overview.totalBuiltArea }}<span class="rpt-kpi-u">km²</span></span>
                <span class="rpt-kpi-l">建设用地总面积</span>
              </div>
              <div v-if="report.overview?.newConstruction != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.overview.newConstruction }}<span class="rpt-kpi-u">km²</span></span>
                <span class="rpt-kpi-l">新增建设面积<MockBadge v-if="report.overview.mock?.newConstruction" /></span>
              </div>
              <div v-if="report.overview?.expansionRate != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.overview.expansionRate }}<span class="rpt-kpi-u">%</span></span>
                <span class="rpt-kpi-l">年均扩张速率<MockBadge v-if="report.overview.mock?.expansionRate" /></span>
              </div>
              <div v-if="report.overview?.rseiMean != null" class="rpt-kpi">
                <span class="rpt-kpi-v" :class="rseiClass">{{ report.overview.rseiMean }}</span>
                <span class="rpt-kpi-l">RSEI 均值 ({{ report.overview.rseiGradeLabel || '—' }})</span>
              </div>
              <div v-if="report.overview?.population != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.overview.population }}<span class="rpt-kpi-u">万人</span></span>
                <span class="rpt-kpi-l">常住人口</span>
              </div>
              <div v-if="report.overview?.gdp != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.overview.gdp }}<span class="rpt-kpi-u">亿元</span></span>
                <span class="rpt-kpi-l">GDP 总量</span>
              </div>
            </div>
            <p v-if="report.overview?.singleYearNote" class="rpt-note">{{ report.overview.singleYearNote }}</p>
          </div>

          <!-- 2. 建设用地扩张 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">2</span>建设用地扩张</h4>
            <p class="rpt-p">{{ report.expansion?.description || '暂无数据。' }}</p>
            <div class="rpt-kpi-row">
              <div v-if="report.expansion?.totalArea != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.expansion.totalArea }}<span class="rpt-kpi-u">km²</span></span>
                <span class="rpt-kpi-l">总面积</span>
              </div>
              <div v-if="report.expansion?.newArea != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.expansion.newArea }}<span class="rpt-kpi-u">km²</span></span>
                <span class="rpt-kpi-l">新增面积<MockBadge v-if="report.expansion.mock?.newArea" /></span>
              </div>
              <div v-if="report.expansion?.patches != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.expansion.patches }}</span>
                <span class="rpt-kpi-l">建设斑块数</span>
                <span class="rpt-kpi-sub">面积÷平均斑块尺度（0.5 km²）</span>
              </div>
              <div v-if="report.expansion?.expansionRate != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.expansion.expansionRate }}<span class="rpt-kpi-u">%</span></span>
                <span class="rpt-kpi-l">扩张速率 (CAGR)<MockBadge v-if="report.expansion.mock?.expansionRate" /></span>
              </div>
            </div>
            <div v-if="report.expansion?.districtRanking?.length" class="rpt-chart-wrap">
              <h5 class="rpt-chart-lbl">区县建设用地排名</h5>
              <div ref="rptRankChartRef" class="rpt-chart" />
            </div>
          </div>

          <!-- 3. 生态响应 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">3</span>生态响应</h4>
            <p class="rpt-p">{{ report.ecology?.description || '暂无数据。' }}</p>
            <div class="rpt-kpi-row">
              <div v-if="report.ecology?.rseiMean != null" class="rpt-kpi">
                <span class="rpt-kpi-v" :class="rseiClass">{{ report.ecology.rseiMean }}</span>
                <span class="rpt-kpi-l">RSEI 均值 ({{ report.ecology.rseiGradeLabel || '—' }})</span>
              </div>
              <div v-if="report.ecology?.rseiChange != null" class="rpt-kpi">
                <span class="rpt-kpi-v" :class="report.ecology.rseiChange > 0 ? 'val-green' : 'val-red'">
                  {{ report.ecology.rseiChange > 0 ? '+' : '' }}{{ report.ecology.rseiChange }}
                </span>
                <span class="rpt-kpi-l">{{ report.ecology.changeDirection || 'RSEI 变化' }}</span>
              </div>
            </div>
            <div v-if="report.ecology?.trendData?.length > 1" class="rpt-chart-wrap">
              <h5 class="rpt-chart-lbl">RSEI 时序变化</h5>
              <div ref="rptRseiChartRef" class="rpt-chart" />
            </div>
            <div v-if="report.ecology?.gradeDistribution?.length" class="rpt-chart-wrap">
              <h5 class="rpt-chart-lbl">生态等级分布</h5>
              <div ref="rptGradeChartRef" class="rpt-chart" />
            </div>
            <div v-if="report.ecology?.changeDistribution?.length" class="rpt-chart-wrap">
              <h5 class="rpt-chart-lbl">生态变化面积分布</h5>
              <div ref="rptChangeChartRef" class="rpt-chart" />
            </div>
          </div>

          <!-- 4. 社会经济 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">4</span>社会经济</h4>
            <p class="rpt-p">{{ report.socio?.description || '暂无数据。' }}</p>
            <div class="rpt-kpi-row">
              <div v-if="report.socio?.population?.total != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.socio.population.total }}<span class="rpt-kpi-u">万人</span></span>
                <span class="rpt-kpi-l">常住人口<span v-if="report.socio.population.growth != null">({{ report.socio.population.growth }}%/年)</span></span>
              </div>
              <div v-if="report.socio?.gdp?.total != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.socio.gdp.total }}<span class="rpt-kpi-u">亿人民币</span></span>
                <span class="rpt-kpi-l">GDP 总量 (PPP)<span v-if="report.socio.gdp.growth != null">({{ report.socio.gdp.growth }}%/年)</span></span>
              </div>
              <div v-if="report.socio?.gdp?.perCapita != null" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.socio.gdp.perCapita }}<span class="rpt-kpi-u">万元</span></span>
                <span class="rpt-kpi-l">人均 GDP</span>
              </div>
            </div>
            <div v-if="report.socio?.gdp?.structure?.length" class="rpt-chart-wrap">
              <h5 class="rpt-chart-lbl">产业结构<MockBadge v-if="report.socio.mock?.industryStructure" /></h5>
              <div ref="rptIndustryChartRef" class="rpt-chart" style="height:140px" />
            </div>
          </div>

          <!-- 5. 耦合关系 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">5</span>耦合关系</h4>
            <p class="rpt-p">{{ couplingText }}</p>
            <div v-if="report.coupling?.correlation != null" class="rpt-kpi-row">
              <div class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.coupling.correlation }}</span>
                <span class="rpt-kpi-l">扩张-生态相关系数</span>
              </div>
              <div v-if="report.coupling.strongNegativeCount" class="rpt-kpi">
                <span class="rpt-kpi-v">{{ report.coupling.strongNegativeCount }}</span>
                <span class="rpt-kpi-l">强负相关区县数</span>
              </div>
            </div>
          </div>

          <!-- 6. 数据说明 -->
          <div class="rpt-sec">
            <h4 class="rpt-sec-title"><span class="rpt-num">6</span>数据说明</h4>
            <div v-if="report.meta?.data_sources?.length || report.overview?.dataSources?.length" class="rpt-src-row">
              <span class="rpt-src-lbl">数据来源：</span>
              <span v-for="src in (report.meta?.data_sources || report.overview?.dataSources)" :key="src" class="rpt-src-tag">{{ src }}</span>
            </div>
            <p class="rpt-disc">
              本报告基于遥感影像反演与栅格统计数据自动生成。部分指标（标注"估算数据"）为经验公式或统计模型估算值，仅供参考。GDP 数据采用购买力平价（PPP）换算，汇率为 {{ GDP_RATE }}。
            </p>
          </div>
        </div>
      </div>
    </template>
  </MapLayout>
  <CustomReportDialog
    v-model="showReportDialog"
    :report="report"
    :study-area="report?.overview?.studyArea || '自定义研究区'"
    :years="report?.meta?.years || report?.overview?.years || []"
  />
  <CompareDialog v-if="report" v-model="showCompare" :default-range="customCompareRange" storage-key="compare-range-custom" />
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import mapboxgl from 'mapbox-gl'
import { Switch } from '@element-plus/icons-vue'
import MapLayout from '../components/layout/MapLayout.vue'
import MapViewer from '../components/map/MapViewer.vue'
import CustomAreaPanel from '../components/custom/CustomAreaPanel.vue'
import MockBadge from '../components/common/MockBadge.vue'
import CustomReportDialog from '../components/custom/CustomReportDialog.vue'
import CustomLayerControl from '../components/map/CustomLayerControl.vue'
import CustomLegendBar from '../components/map/CustomLegendBar.vue'
import BottomBar from '../components/layout/BottomBar.vue'
import CompareDialog from '../components/dialog/CompareDialog.vue'
import { buildWmsTileUrlFromUrl } from '../utils/geoserver'
import { nextCustomLayerLoadState } from '../utils/customLayerState'
import { TIME_PERIODS } from '../config/map'

import { getAnalysis, getComputeProgress, cancelCompute } from '../api'

const route = useRoute()
const router = useRouter()
const mapRef = ref(null)
const panelRef = ref(null)
const report = ref(null)
const computing = ref(false)
const progressData = ref({ percent: 0, step: '', year: null, taskId: null })
const mapInstance = ref(null)
const pendingBoundary = ref(null)
let progressTimer = null
let beforeUnloadHandler = null
let loadGeneration = 0
const addedLayerIds = []
const showReportDialog = ref(false)
const showCompare = ref(false)
const mapLayers = ref([])
const visibleTypes = ref([])
const pendingMapLayers = ref([])

// ─── 双期对比: derive range from report data ───
const customCompareRange = computed(() => {
  const years = report.value?.meta?.years || report.value?.overview?.years || []
  if (years.length >= 2) return [years[0], years[years.length - 1]]
  // Fallback: TIME_PERIODS first→last (should rarely happen when report exists)
  return [TIME_PERIODS[0], TIME_PERIODS[TIME_PERIODS.length - 1]]
})

function loadCustomRange() {
  try {
    const raw = localStorage.getItem('compare-range-custom')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length === 2) return parsed
    }
  } catch { /* ignore */ }
  return customCompareRange.value
}

const customBottomItems = computed(() => {
  const [start, end] = loadCustomRange()
  return [
    { key: 'compare', label: '双期对比', sub: `${start} → ${end}`, icon: Switch },
  ]
})

function onBottomBarClick(item) {
  if (item.key === 'compare') showCompare.value = true
}

// Chart refs
const gradeChartRef = ref(null)
const trendChartRef = ref(null)
const changeChartRef = ref(null)
const radarChartRef = ref(null)
const expBarChartRef = ref(null)
const expModeBarRef = ref(null)
const scatterChartRef = ref(null)
const industryPieRef = ref(null)
const popBarRef = ref(null)
const gdpBarRef = ref(null)
const chartInstances = []

// Report tab chart refs
const rptRankChartRef = ref(null)
const rptRseiChartRef = ref(null)
const rptGradeChartRef = ref(null)
const rptChangeChartRef = ref(null)
const rptIndustryChartRef = ref(null)
const rptChartInstances = []

const tabs = [
  { key: 'overview', label: '总览', color: '#FFD43B' },
  { key: 'ecology', label: '生态评估', color: '#51CF66' },
  { key: 'construction', label: '建设用地', color: '#FF6B6B' },
  { key: 'socio', label: '经济统计', color: '#4DABF7' },
  { key: 'tasks', label: '任务列表', color: '#20C997' },
  { key: 'placeholder', label: '占位', color: '#868E96' },
  { key: 'report', label: '分析报告', color: '#F783AC' },
]

const overview = computed(() => report.value?.overview || {})
const progressStatus = computed(() => progressData.value.percent >= 100 ? 'success' : '')
const rseiChangeColor = computed(() => {
  const v = report.value?.ecology?.rseiChange
  if (v == null) return ''
  return v >= 0 ? '#69DB7C' : '#FF6B6B'
})

function fmt(val, dec = 1) {
  if (val === null || val === undefined || val === '') return '—'
  return typeof val === 'number' ? val.toFixed(dec) : val
}

// ─── Chart rendering ───

function disposeCharts() {
  chartInstances.forEach(i => { try { i.dispose() } catch {} })
  chartInstances.length = 0
}

function initChart(el) {
  if (!el) return null
  const inst = echarts.init(el)
  chartInstances.push(inst)
  return inst
}

function renderCharts() {
  disposeCharts()
  nextTick(() => {
    renderEcologyCharts()
    renderExpansionCharts()
    renderSocioCharts()
    renderCouplingChart()
  })
}

// ─── 切回含图表的 tab 时重播动画 ───
// MapLayout 在 activeTab 变化时会 dispatch 'chart-replay' 事件，
// 此处仅销毁该 tab 对应的 ECharts 实例并重新渲染，触发入场动画。

const TAB_CHART_RENDERERS = {
  ecology: {
    getRefs: () => [gradeChartRef, trendChartRef, changeChartRef, radarChartRef],
    render: renderEcologyCharts,
  },
  construction: {
    getRefs: () => [expBarChartRef, expModeBarRef],
    render: renderExpansionCharts,
  },
  socio: {
    getRefs: () => [industryPieRef, popBarRef, gdpBarRef],
    render: renderSocioCharts,
  },
  report: {
    getRefs: () => [rptRankChartRef, rptRseiChartRef, rptGradeChartRef, rptChangeChartRef, rptIndustryChartRef],
    render: renderReportCharts,
    dispose: disposeReportCharts,
  },
}

function replayChartsForTab(tabKey) {
  const entry = TAB_CHART_RENDERERS[tabKey]
  if (!entry || !report.value) return
  if (entry.dispose) {
    // Report tab uses its own instance array — delegate dispose
    entry.dispose()
  } else {
    const elements = new Set(entry.getRefs().map(r => r.value).filter(Boolean))
    for (let i = chartInstances.length - 1; i >= 0; i--) {
      const inst = chartInstances[i]
      let dom = null
      try { dom = inst.getDom() } catch { continue }
      if (dom && elements.has(dom)) {
        try { inst.dispose() } catch {}
        chartInstances.splice(i, 1)
      }
    }
  }
  nextTick(() => entry.render())
}

function onChartReplay(e) {
  const key = e?.detail
  if (typeof key === 'string') {
    replayChartsForTab(key)
    // 切到任务列表时自动刷新
    if (key === 'tasks' && panelRef.value) {
      panelRef.value.fetchTasks()
    }
  }
}

function renderEcologyCharts() {
  const eco = report.value?.ecology
  if (!eco) return

  // Grade bar chart
  if (gradeChartRef.value && eco.gradeDistribution?.length) {
    const inst = initChart(gradeChartRef.value)
    const gradeData = eco.gradeDistribution
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${p[0].name}<br/>面积: ${p[0].value} km²` },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: gradeData.map(d => d.grade + '\n' + (d.range || '')),
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#ccc', fontSize: 10, lineHeight: 14 },
        name: '生态等级',
        nameLocation: 'middle',
        nameGap: 32,
        nameTextStyle: { color: '#888', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        name: '面积 (km²)',
        nameTextStyle: { color: '#888', fontSize: 10 },
        axisLabel: { color: '#888', fontSize: 10 },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [{ type: 'bar', barWidth: '50%', data: gradeData.map(d => ({ value: d.area, itemStyle: { color: d.color, borderRadius: [3, 3, 0, 0] } })) }],
    })
  }

  // Trend line chart
  if (trendChartRef.value && eco.trendData?.length) {
    const inst = initChart(trendChartRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: { type: 'category', data: eco.trendData.map(d => d.year), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 11 } },
      yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      series: [{ type: 'line', data: eco.trendData.map(d => d.value), smooth: true, symbol: 'circle', symbolSize: 8, lineStyle: { color: '#51CF66', width: 2 }, itemStyle: { color: '#51CF66' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(81,207,102,0.3)' }, { offset: 1, color: 'rgba(81,207,102,0.05)' }]) } }],
    })
  }

  // Change pie chart
  if (changeChartRef.value && eco.changeDistribution?.length) {
    const inst = initChart(changeChartRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} km²' },
      series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'], avoidLabelOverlap: false, itemStyle: { borderRadius: 4, borderColor: '#1a1a1a', borderWidth: 2 }, label: { show: true, fontSize: 10, color: '#ccc', formatter: '{b}\n{c}km²' }, labelLine: { lineStyle: { color: '#666' } }, data: eco.changeDistribution.map(d => ({ name: d.name, value: d.area, itemStyle: { color: d.color } })) }],
    })
  }

  // Radar chart
  if (radarChartRef.value && eco.fourIndicators) {
    const fi = eco.fourIndicators
    const inst = initChart(radarChartRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: {},
      radar: { center: ['50%', '50%'], radius: '60%', indicator: [{ name: 'NDVI/绿度', max: 1 }, { name: 'Wet/湿度', max: 1 }, { name: 'NDBSI/干度', max: 1 }, { name: 'LST/热度', max: 1 }], axisName: { color: '#aaa', fontSize: 10 }, shape: 'circle', splitNumber: 4, axisLine: { lineStyle: { color: '#444' } }, splitLine: { lineStyle: { color: '#333' } }, splitArea: { areaStyle: { color: ['#1a1a1a', '#1a1a1a'] } } },
      series: [{ type: 'radar', data: [{ value: [fi.ndvi || 0, fi.wet || 0, fi.ndbsi || 0, fi.lst || 0], name: overview.value.studyArea || '研究区', symbol: 'circle', symbolSize: 4, lineStyle: { width: 1.5, color: '#51CF66' }, areaStyle: { color: 'rgba(81,207,102,0.2)' }, itemStyle: { color: '#51CF66' } }] }],
    })
  }
}

function renderExpansionCharts() {
  const exp = report.value?.expansion
  if (!exp) return

  // District bar chart (used in both expansion tab and built-area tab)
  const districtData = exp.districtRanking?.slice(0, 15)
  if (expBarChartRef.value && districtData?.length) {
    const inst = initChart(expBarChartRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      yAxis: { type: 'category', data: districtData.map(d => d.name).reverse(), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 11 }, axisTick: { show: false } },
      series: [{ type: 'bar', data: districtData.map(d => d.value).reverse(), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FF6B6B' }, { offset: 1, color: '#FFA94D' }]), borderRadius: [0, 3, 3, 0] }, barWidth: '60%' }],
    })
  }
  if (expModeBarRef.value && districtData?.length) {
    const inst = initChart(expModeBarRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      yAxis: { type: 'category', data: districtData.map(d => d.name).reverse(), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 11 }, axisTick: { show: false } },
      series: [{ type: 'bar', data: districtData.map(d => d.value).reverse(), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FF6B6B' }, { offset: 1, color: '#FFA94D' }]), borderRadius: [0, 3, 3, 0] }, barWidth: '60%' }],
    })
  }
}

function renderSocioCharts() {
  const socio = report.value?.socio
  if (!socio) return

  // Industry pie
  if (industryPieRef.value && socio.industryStructure?.length) {
    const inst = initChart(industryPieRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
      series: [{ type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'], itemStyle: { borderRadius: 4, borderColor: '#1a1a1a', borderWidth: 2 }, label: { show: true, fontSize: 11, color: '#ccc', formatter: '{b}\n{c}%' }, labelLine: { lineStyle: { color: '#666' } }, data: socio.industryStructure.map(d => ({ name: d.name, value: d.value, itemStyle: { color: d.color } })) }],
    })
  }

  // Population bar
  if (popBarRef.value && socio.districtPopulation?.length) {
    const data = socio.districtPopulation.slice(0, 12)
    const inst = initChart(popBarRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      yAxis: { type: 'category', data: data.map(d => d.name).reverse(), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 10 }, axisTick: { show: false } },
      series: [{ type: 'bar', data: data.map(d => d.value).reverse(), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#748FFC' }, { offset: 1, color: '#4DABF7' }]), borderRadius: [0, 3, 3, 0] }, barWidth: '60%' }],
    })
  }

  // GDP bar
  if (gdpBarRef.value && socio.districtGdp?.length) {
    const data = socio.districtGdp.slice(0, 12)
    const inst = initChart(gdpBarRef.value)
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${p[0].name}<br/>GDP: ${p[0].value} 亿人民币` },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      yAxis: { type: 'category', data: data.map(d => d.name).reverse(), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 10 }, axisTick: { show: false } },
      series: [{ type: 'bar', data: data.map(d => d.value).reverse(), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#F783AC' }, { offset: 1, color: '#FF6B6B' }]), borderRadius: [0, 3, 3, 0] }, barWidth: '60%' }],
    })
  }
}

function renderCouplingChart() {
  const coupling = report.value?.coupling
  if (!scatterChartRef.value || !coupling?.scatterData?.length) return

  const inst = initChart(scatterChartRef.value)
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: (p) => `${p.data[2]}<br/>建设用地: ${p.data[0]} km²<br/>RSEI: ${p.data[1]}` },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
    xAxis: { name: '建设用地(km²)', nameTextStyle: { color: '#888' }, axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } } },
    yAxis: { name: 'RSEI 均值', nameTextStyle: { color: '#888' }, axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } } },
    series: [{ type: 'scatter', symbolSize: 16, data: coupling.scatterData.map(d => [d.expansionRate, d.rseiChange, d.name]), itemStyle: { color: (p) => { const y = p.data[1]; return y < -0.05 ? '#FF6B6B' : y < -0.02 ? '#FFD43B' : '#69DB7C' } } }],
  })
}

// ─── Report tab charts ───
function disposeReportCharts() {
  rptChartInstances.forEach(i => { try { i.dispose() } catch {} })
  rptChartInstances.length = 0
}

function initReportChart(el, height) {
  if (!el) return null
  if (height) el.style.height = height + 'px'
  const inst = echarts.init(el)
  rptChartInstances.push(inst)
  return inst
}

function renderReportCharts() {
  disposeReportCharts()
  nextTick(() => {
    const dark = { backgroundColor: 'transparent' }
    const grid = { left: '3%', right: '4%', bottom: '3%', top: '12%', containLabel: true }
    const darkAxis = {
      axisLabel: { color: '#aaa' },
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#2a2a2a' } },
    }

    if (rptRankChartRef.value && report.value?.expansion?.districtRanking?.length) {
      const data = report.value.expansion.districtRanking.slice(0, 12)
      const rankGrid = { left: '3%', right: '8%', bottom: '15%', top: '6%', containLabel: true }
      const chartHeight = data.length * 28 + 20
      initReportChart(rptRankChartRef.value, chartHeight).setOption({
        ...dark, tooltip: { trigger: 'axis' }, grid: rankGrid,
        xAxis: { type: 'value', ...darkAxis },
        yAxis: { type: 'category', data: data.map(d => d.name).reverse(), ...darkAxis,
          axisLabel: { ...darkAxis.axisLabel, fontSize: 11 },
        },
        series: [{
          type: 'bar', data: data.map(d => d.value).reverse(),
          itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FF6B6B' }, { offset: 1, color: '#FFA94D' }]), borderRadius: [0, 4, 4, 0] },
        }],
      })
    }

    if (rptRseiChartRef.value && report.value?.ecology?.trendData?.length > 1) {
      initReportChart(rptRseiChartRef.value).setOption({
        ...dark, tooltip: { trigger: 'axis' }, grid,
        xAxis: { type: 'category', data: report.value.ecology.trendData.map(d => d.year), ...darkAxis },
        yAxis: { type: 'value', min: 0, max: 1, ...darkAxis },
        series: [{
          type: 'line', data: report.value.ecology.trendData.map(d => d.value), smooth: true,
          lineStyle: { color: '#51CF66', width: 2 }, itemStyle: { color: '#51CF66' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(81,207,102,0.25)' }, { offset: 1, color: 'rgba(81,207,102,0.03)' }]) },
        }],
      })
    }

    if (rptGradeChartRef.value && report.value?.ecology?.gradeDistribution?.length) {
      initReportChart(rptGradeChartRef.value).setOption({
        ...dark, tooltip: { trigger: 'axis' }, grid,
        xAxis: { type: 'category', data: report.value.ecology.gradeDistribution.map(d => d.grade), ...darkAxis },
        yAxis: { type: 'value', ...darkAxis },
        series: [{ type: 'bar', barWidth: '50%', data: report.value.ecology.gradeDistribution.map(d => ({ value: d.area, itemStyle: { color: d.color } })) }],
      })
    }

    if (rptChangeChartRef.value && report.value?.ecology?.changeDistribution?.length) {
      initReportChart(rptChangeChartRef.value).setOption({
        ...dark, tooltip: { trigger: 'axis' }, grid,
        xAxis: { type: 'category', data: report.value.ecology.changeDistribution.map(d => d.name), ...darkAxis },
        yAxis: { type: 'value', ...darkAxis },
        series: [{ type: 'bar', barWidth: '50%', data: report.value.ecology.changeDistribution.map(d => ({ value: d.area, itemStyle: { color: d.color } })) }],
      })
    }

    if (rptIndustryChartRef.value && report.value?.socio?.gdp?.structure?.length) {
      initReportChart(rptIndustryChartRef.value).setOption({
        ...dark, tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
        series: [{ type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'], data: report.value.socio.gdp.structure.map(d => ({ name: d.name, value: d.value, itemStyle: { color: d.color } })), label: { color: '#ccc', fontSize: 11, formatter: '{b}\n{c}%' } }],
      })
    }
  })
}

// ─── Task selection ───
async function onTaskSelect(task) {
  // 切换任务时，先停止之前的进度轮询和计算状态
  stopProgressPolling()
  computing.value = false
  uninstallBeforeUnload()

  const gen = ++loadGeneration
  const taskId = task.task_id || task.id
  const years = task.time_periods || task.years || []
  report.value = null
  try {
    const data = await getAnalysis(taskId)
    if (gen !== loadGeneration) return  // 用户已切换到其他任务
    if (data.status === 'failed') { ElMessage.error(data.error || '计算失败'); return }
    if (data.status === 'processing' || data.status === 'pending') {
      computing.value = true
      startProgressPolling(taskId)
      installBeforeUnload()
      return
    }

    // 先启动纯飞行动画，等动画完全结束后再加载 report + 图表
    const layerData = data.map_layers || null
    const loadReport = () => {
      if (gen !== loadGeneration) return  // 动画期间用户已切换任务
      report.value = data.report || data
      renderCharts()
      if (layerData) addMapLayers(layerData)
    }

    if (data.boundary_geojson) {
      addBoundaryGeoJSON(data.boundary_geojson, loadReport)
    } else {
      loadReport()
    }
  } catch (err) {
    if (gen !== loadGeneration) return
    ElMessage.error(err.response?.data?.detail || '加载失败')
  }
}

function onTaskDeselect() {
  report.value = null
  computing.value = false
  removeMapLayers()
  disposeCharts()
  stopProgressPolling()
}

// ─── Progress ───
function startProgressPolling(taskId) {
  stopProgressPolling()
  async function poll() {
    try {
      const data = await getComputeProgress(taskId)
      progressData.value = { percent: data.progress || 0, step: data.current_step || '', year: data.current_year, taskId }
      if (data.status === 'completed') {
        computing.value = false; stopProgressPolling(); uninstallBeforeUnload()
        const gen = loadGeneration
        const full = await getAnalysis(taskId)
        if (gen !== loadGeneration) return  // 用户已切换任务
        const layerData = full.map_layers || null
        const loadReport = () => {
          if (gen !== loadGeneration) return
          report.value = full.report || full
          renderCharts()
          if (layerData) addMapLayers(layerData)
        }
        if (full.boundary_geojson) {
          addBoundaryGeoJSON(full.boundary_geojson, loadReport)
        } else {
          loadReport()
        }
        ElMessage.success('计算完成！')
        return
      }
      if (data.status === 'failed') { computing.value = false; stopProgressPolling(); uninstallBeforeUnload(); ElMessage.error('计算失败'); return }
      if (data.status === 'cancelled') { computing.value = false; stopProgressPolling(); uninstallBeforeUnload(); ElMessage.info('已取消'); return }
    } catch { /* retry */ }
  }
  poll()
  progressTimer = setInterval(poll, 3000)
}
function stopProgressPolling() { if (progressTimer) { clearInterval(progressTimer); progressTimer = null } }
async function cancelTask() { try { await cancelCompute(progressData.value.taskId); ElMessage.info('已发送取消请求') } catch { ElMessage.error('取消失败') } }

function installBeforeUnload() { beforeUnloadHandler = (e) => { e.preventDefault(); e.returnValue = '' }; window.addEventListener('beforeunload', beforeUnloadHandler) }
function uninstallBeforeUnload() { if (beforeUnloadHandler) { window.removeEventListener('beforeunload', beforeUnloadHandler); beforeUnloadHandler = null } }

// ─── Map ───
function onMapLoaded(map) {
  mapInstance.value = map
  if (pendingBoundary.value) { addBoundaryGeoJSON(pendingBoundary.value); pendingBoundary.value = null }
  if (pendingMapLayers.value.length) {
    const layers = pendingMapLayers.value
    pendingMapLayers.value = []
    registerMapLayers(layers)
  }
}
function addMapLayers(layers) {
  clearRegisteredMapLayers()
  const nextState = nextCustomLayerLoadState(layers, !!mapInstance.value)
  mapLayers.value = nextState.mapLayers
  pendingMapLayers.value = nextState.pendingLayers
  // 所有图层默认关闭，由用户手动打开
  visibleTypes.value = []
  // 从后端配置中读取默认可见图层（已禁用，因已有旧数据写入 visible: true）
  // visibleTypes.value = nextState.mapLayers.filter(l => l.visible).map(l => l.type)
  if (nextState.shouldRegister) registerMapLayers(nextState.mapLayers)
}

function registerMapLayers(layers) {
  if (!mapInstance.value) return
  // Add all WMS sources/layers; track visibility per layer
  for (const layer of layers) {
    if (!layer.wms_url) continue
    const sourceId = `custom-${layer.type}`, layerId = `custom-${layer.type}`
    mapInstance.value.addSource(sourceId, { type: 'raster', tiles: [buildWmsTileUrlFromUrl(layer.wms_url)], tileSize: 256 })
    mapInstance.value.addLayer({ id: layerId, type: 'raster', source: sourceId, paint: { 'raster-opacity': 0.7 } })
    addedLayerIds.push(layerId)
    // 后端 visible: true 的图层初始可见
    const isVisible = visibleTypes.value.includes(layer.type)
    mapInstance.value.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none')
  }
}

function clearRegisteredMapLayers() {
  if (!mapInstance.value) {
    addedLayerIds.length = 0
    return
  }
  for (const layerId of addedLayerIds) {
    let sourceId = null
    try { sourceId = mapInstance.value.getLayer(layerId)?.source } catch {}
    try { mapInstance.value.removeLayer(layerId) } catch {}
    if (sourceId) {
      try { mapInstance.value.removeSource(sourceId) } catch {}
    }
  }
  addedLayerIds.length = 0
}

function removeMapLayers() {
  pendingMapLayers.value = []
  clearRegisteredMapLayers()
  mapLayers.value = []
  visibleTypes.value = []
}

function onLayerToggle({ type, visible }) {
  if (!mapInstance.value) return
  const layerId = `custom-${type}`
  try {
    if (visible) {
      mapInstance.value.setLayoutProperty(layerId, 'visibility', 'visible')
      if (!visibleTypes.value.includes(type)) visibleTypes.value = [...visibleTypes.value, type]
    } else {
      mapInstance.value.setLayoutProperty(layerId, 'visibility', 'none')
      visibleTypes.value = visibleTypes.value.filter(t => t !== type)
    }
  } catch (e) {
    console.warn('layer toggle failed:', e)
  }
}
function removeBoundaryLayers() {
  if (!mapInstance.value) return
  try {
    if (mapInstance.value.getLayer('boundary-fill')) mapInstance.value.removeLayer('boundary-fill')
    if (mapInstance.value.getLayer('boundary-line')) mapInstance.value.removeLayer('boundary-line')
    if (mapInstance.value.getSource('boundary-src')) mapInstance.value.removeSource('boundary-src')
  } catch {}
}

function addBoundaryGeoJSON(geojson, onSettled) {
  if (!mapInstance.value) { pendingBoundary.value = geojson; if (onSettled) onSettled(); return }

  // 计算 bbox
  let bounds = null
  try {
    let coords = null
    if (geojson.type === 'FeatureCollection' && geojson.features?.[0]) coords = geojson.features[0].geometry.coordinates[0]
    else if (geojson.type === 'Polygon') coords = geojson.coordinates[0]
    else if (geojson.type === 'MultiPolygon') coords = geojson.coordinates[0][0]
    if (coords?.length) {
      bounds = new mapboxgl.LngLatBounds(coords[0], coords[0])
      for (const [lng, lat] of coords) bounds.extend([lng, lat])
    }
  } catch {}

  // 动画前清掉旧图层
  removeBoundaryLayers()

  // 计算目标相机
  let targetCamera = { center: [116.4, 39.9], zoom: 7 }
  if (bounds) {
    const camera = mapInstance.value.cameraForBounds(bounds, { padding: 80 })
    if (camera) targetCamera = camera
  }

  // 判断距离：用 zoom 8 瓦片坐标差衡量，≤2 格用 flyTo，否则 jumpTo
  const currentCenter = mapInstance.value.getCenter()
  const near = isNearby(
    [currentCenter.lng, currentCenter.lat],
    [targetCamera.center[0], targetCamera.center[1]],
    mapInstance.value.getZoom(),
    targetCamera.zoom,
  )

  if (near) {
    // ── 近距离：flyTo 飞行动画 + 边界渐显 ──
    mapInstance.value.flyTo({
      center: targetCamera.center,
      zoom: targetCamera.zoom,
      duration: 1500,
      essential: true,
    })
    mapInstance.value.once('moveend', () => {
      if (!mapInstance.value) return
      addBoundaryLayers(geojson, 0, 0)
      fadeBoundaryIn(0.15, 1, 600, onSettled)
    })
  } else {
    // ── 远距离：jumpTo 瞬移 + 边界渐显 ──
    mapInstance.value.jumpTo({
      center: targetCamera.center,
      zoom: targetCamera.zoom,
    })
    addBoundaryLayers(geojson, 0, 0)
    fadeBoundaryIn(0.15, 1, 600, onSettled)
  }
}

// 添加边界图层
function addBoundaryLayers(geojson, fillOpacity, lineOpacity) {
  if (!mapInstance.value) return
  try {
    let gd = geojson
    if (geojson.type === 'Polygon' || geojson.type === 'MultiPolygon') gd = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: geojson }] }
    mapInstance.value.addSource('boundary-src', { type: 'geojson', data: gd })
    mapInstance.value.addLayer({ id: 'boundary-fill', type: 'fill', source: 'boundary-src', paint: { 'fill-color': '#FF9F43', 'fill-opacity': fillOpacity } })
    mapInstance.value.addLayer({ id: 'boundary-line', type: 'line', source: 'boundary-src', paint: { 'line-color': '#FF9F43', 'line-width': 2, 'line-opacity': lineOpacity } })
  } catch (e) { console.warn('boundary error:', e) }
}

// 边界渐显动画
function fadeBoundaryIn(fillTarget, lineTarget, duration, onDone) {
  const start = performance.now()
  function animate(now) {
    const t = Math.min((now - start) / duration, 1)
    const ease = t * (2 - t) // easeOutQuad
    if (mapInstance.value) {
      try {
        mapInstance.value.setPaintProperty('boundary-fill', 'fill-opacity', fillTarget * ease)
        mapInstance.value.setPaintProperty('boundary-line', 'line-opacity', lineTarget * ease)
      } catch {}
    }
    if (t < 1) requestAnimationFrame(animate)
    else if (onDone) requestAnimationFrame(() => onDone())
  }
  requestAnimationFrame(animate)
}

// 判断两点是否在附近瓦片范围内
// zoom 8 下瓦片差 ≤2 → 近距离（约 300km 以内），可用 flyTo
function isNearby(center1, center2, zoom1, zoom2) {
  const refZoom = 8
  const t1 = toTileCoord(center1, refZoom)
  const t2 = toTileCoord(center2, refZoom)
  const tileDist = Math.max(Math.abs(t1.x - t2.x), Math.abs(t1.y - t2.y))
  const zoomDiff = Math.abs(zoom1 - zoom2)
  return tileDist <= 2 && zoomDiff <= 1
}

// 经纬度 → 瓦片坐标
function toTileCoord([lng, lat], zoom) {
  const n = Math.pow(2, zoom)
  const x = ((lng + 180) / 360) * n
  const y = (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n
  return { x, y }
}

// Resize
watch(report, () => nextTick(() => chartInstances.forEach(i => i.resize())))

// 从上传页跳转过来时，延迟刷新任务面板（后端可能刚创建任务）
onMounted(() => {
  window.addEventListener('chart-replay', onChartReplay)
  if (route.query.submitted === '1') {
    router.replace({ path: '/custom-area', query: {} }) // 清掉 query 参数
    setTimeout(() => {
      if (panelRef.value) panelRef.value.fetchTasks()
    }, 2500)
  }
})

onUnmounted(() => {
  window.removeEventListener('chart-replay', onChartReplay)
  stopProgressPolling(); uninstallBeforeUnload(); removeMapLayers(); disposeCharts()
})
</script>

<style scoped>
/* Panel content */
.panel-content { padding: 12px }
.panel-title { font-size: 14px; font-weight: 600; color: #ddd; margin: 0 0 12px }
.hint { color: #666; font-size: 13px; text-align: center; padding: 40px 16px }

/* Task section in overview */
.task-section { border-bottom: 1px solid #333; max-height: 280px; overflow-y: auto; flex-shrink: 0 }

/* Progress */
.progress-overlay { padding: 16px; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; margin: 12px }
.progress-step { color: #aaa; font-size: 13px; margin: 8px 0 4px }
.progress-warn { color: #FF922B; font-size: 12px; margin: 0 0 8px }

/* ─── Report header ─── */
.report-header {
  padding: 12px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  margin-bottom: 10px;
}
.header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}
.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.meta-tag {
  font-size: 11px;
  color: #aaa;
  background: #252525;
  padding: 2px 8px;
  border-radius: 4px;
}

/* ─── RSEI grade badge ─── */
.rsei-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  color: #fff;
}
.rsei-badge.excellent { background: #2B8A3E }
.rsei-badge.good { background: #69DB7C; color: #1a1a1a }
.rsei-badge.moderate { background: #FFD43B; color: #1a1a1a }
.rsei-badge.poor { background: #FF922B }
.rsei-badge.bad { background: #FF6B6B }

.grade-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  color: #fff;
}
.grade-badge.excellent { background: #2B8A3E }
.grade-badge.good { background: #69DB7C; color: #1a1a1a }
.grade-badge.moderate { background: #FFD43B; color: #1a1a1a }
.grade-badge.poor { background: #FF922B }
.grade-badge.bad { background: #FF6B6B }
.grade-hint {
  font-size: 10px;
  color: #666;
  margin-left: 4px;
}
.stat-grade {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* ─── Conclusion ─── */
.conclusion-box {
  background: #1a1a1a;
  border-left: 3px solid #FFD43B;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.conclusion-label {
  font-size: 11px;
  font-weight: 600;
  color: #FFD43B;
  margin-bottom: 4px;
}
.conclusion-text {
  font-size: 12px;
  color: #bbb;
  line-height: 1.6;
  margin: 0;
}

/* ─── Data sources ─── */
.data-sources {
  padding: 8px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.src-label { font-size: 10px; color: #666; }
.src-tag {
  font-size: 10px;
  color: #888;
  background: #1a1a1a;
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid #2a2a2a;
}

/* ─── Panel description ─── */
.panel-desc {
  background: #1a1a1a;
  border-left: 3px solid #555;
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 12px;
}
.panel-desc p {
  font-size: 12px;
  color: #999;
  line-height: 1.6;
  margin: 0;
}

/* ─── Stat notes & sub-sections ─── */
.stat-note {
  font-size: 10px;
  color: #666;
  margin-top: 4px;
  line-height: 1.4;
}
.stat-unit {
  font-size: 11px;
  font-weight: 400;
  color: #888;
}
.unit-hint {
  font-size: 10px;
  color: #666;
}
.sub-section {
  margin-bottom: 12px;
}
.sub-title {
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
  margin: 0 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #2a2a2a;
}

/* Ecology change direction */
.stat-dir {
  font-size: 11px;
  margin-top: 4px;
  font-weight: 600;
}
.stat-dir.dir-good { color: #69DB7C }
.stat-dir.dir-bad { color: #FF6B6B }

/* Overview grid */
.overview-section { padding: 12px }
.overview-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 8px }
.ind-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 3px }
.ind-head { display: flex; align-items: center; gap: 4px }
.ind-label { color: #888; font-size: 11px }
.ind-value { color: #ddd; font-size: 17px; font-weight: 600 }
.ind-unit { font-size: 11px; font-weight: 400; color: #888 }
.ind-name { font-size: 14px; word-break: break-all }
.eco-good { color: #69DB7C }
.eco-bad { color: #FF6B6B }

/* Stat cards */
.stat-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 14px }
.stat-card { background: #252525; border-radius: 8px; padding: 10px; text-align: center }
.stat-head-row { display: flex; align-items: center; justify-content: center; gap: 4px }
.stat-val { font-size: 20px; font-weight: 700; color: #fff }
.stat-lbl { font-size: 11px; color: #aaa; margin-top: 2px }

/* Charts */
.chart-section { margin-bottom: 14px }
.sec-title { font-size: 12px; font-weight: 600; color: #aaa; margin: 0 0 6px; display: flex; align-items: center; gap: 4px }
.chart-box { height: 150px; background: #252525; border-radius: 8px }
.chart-box.tall { height: 220px }

/* Table */
.table-wrap { overflow-x: auto }
table { width: 100%; border-collapse: collapse; font-size: 12px }
th { background: #222; color: #aaa; padding: 6px 8px; text-align: left; border-bottom: 1px solid #333; white-space: nowrap }
td { color: #bbb; padding: 5px 8px; border-bottom: 1px solid #2a2a2a }

/* Download section — pinned to bottom */
.download-section {
  margin-top: auto;
  padding: 12px;
}
.dl-card {
  display: flex; align-items: center; gap: 10px;
  background: #252525; border: 1px solid #333; border-radius: 8px;
  padding: 12px; cursor: pointer; transition: all 0.2s;
}
.dl-card:hover { border-color: #555; background: #2a2a2a }
.dl-card.disabled { opacity: 0.4; cursor: not-allowed }
.dl-card.disabled:hover { border-color: #333; background: #252525 }
.dl-icon { font-size: 24px; flex-shrink: 0; }
.dl-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.dl-name { color: #ddd; font-size: 13px; font-weight: 600; }
.dl-desc { color: #666; font-size: 11px; }
.dl-arrow { color: #555; font-size: 18px; flex-shrink: 0; }

/* ===== Report tab body ===== */
.rpt-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.rpt-sec {
  background: #252525;
  border-radius: 8px;
  padding: 10px 12px;
}
.rpt-sec-title {
  font-size: 13px;
  font-weight: 700;
  color: #ddd;
  margin: 0 0 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.rpt-num {
  width: 18px; height: 18px; border-radius: 50%;
  background: #fff; color: #1a1a1a;
  font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rpt-p {
  font-size: 12px; color: #aaa; line-height: 1.7;
  margin: 0 0 8px; text-align: justify;
}
.rpt-kpi-row {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-bottom: 8px;
}
.rpt-kpi {
  background: #1e1e1e; border-radius: 6px;
  padding: 6px 10px; min-width: 70px; flex: 1;
  text-align: center;
}
.rpt-kpi-v {
  font-size: 15px; font-weight: 700; color: #e0e0e0;
  display: block; line-height: 1.3;
}
.rpt-kpi-u { font-size: 10px; font-weight: 400; color: #888; }
.rpt-kpi-l {
  font-size: 10px; color: #777; margin-top: 2px;
  display: flex; align-items: center; justify-content: center; gap: 4px;
}
.rpt-kpi-sub {
  font-size: 9px; color: #555; display: block; margin-top: 1px;
}
.rpt-note {
  font-size: 11px; color: #666; background: #1e1e1e;
  padding: 6px 10px; border-radius: 4px; margin-top: 6px;
}
.rpt-chart-wrap { margin-bottom: 8px; }
.rpt-chart-lbl {
  font-size: 11px; font-weight: 600; color: #888;
  margin: 0 0 4px; display: flex; align-items: center; gap: 6px;
}
.rpt-chart { height: 150px; }
.rpt-src-row {
  display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
  margin-bottom: 6px;
}
.rpt-src-lbl { font-size: 11px; color: #888; flex-shrink: 0; }
.rpt-src-tag {
  display: inline-block; background: #1e1e1e; border-radius: 3px;
  padding: 1px 6px; font-size: 10px; color: #aaa;
  border: 1px solid #333;
}
.rpt-disc {
  font-size: 11px; color: #666; line-height: 1.6; text-align: justify;
}
.val-green { color: #69DB7C !important; }
.val-red { color: #FF6B6B !important; }
.val-excellent { color: #2B8A3E !important; }
.val-moderate { color: #FFD43B !important; }
.val-orange { color: #FF922B !important; }
</style>
