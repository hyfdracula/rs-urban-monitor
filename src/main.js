import { createApp } from 'vue'
import {
  ElAlert,
  ElAutocomplete,
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDatePicker,
  ElDialog,
  ElIcon,
  ElInput,
  ElLoading,
  ElProgress,
  ElRadio,
  ElRadioGroup,
  ElStep,
  ElSteps,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
  ElUpload,
} from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import {
  Aim,
  Expand,
  InfoFilled,
  Location,
  MoonNight,
  OfficeBuilding,
  Position,
  Share,
  Sunny,
  Switch,
  TrendCharts,
  User,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

const elementComponents = [
  ElAlert,
  ElAutocomplete,
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDatePicker,
  ElDialog,
  ElIcon,
  ElInput,
  ElProgress,
  ElRadio,
  ElRadioGroup,
  ElStep,
  ElSteps,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
  ElUpload,
]

for (const component of elementComponents) {
  app.use(component)
}

const globalIcons = {
  Aim,
  Expand,
  InfoFilled,
  Location,
  MoonNight,
  OfficeBuilding,
  Position,
  Share,
  Sunny,
  Switch,
  TrendCharts,
  User,
  Warning,
  WarningFilled,
}

for (const [name, component] of Object.entries(globalIcons)) {
  app.component(name, component)
}

app.use(ElLoading)
app.use(router)
app.mount('#app')
