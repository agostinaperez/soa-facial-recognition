import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'
import router from './router'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          background: '#0d1117',
          surface: '#161b22',
          'surface-variant': '#21262d',
          primary: '#388bfd',
          secondary: '#3fb950',
          error: '#f85149',
          warning: '#d29922',
          info: '#58a6ff',
          success: '#3fb950',
        },
        variables: {
          'field-input-padding-top': '8px',
          'theme-on-surface': '#e6edf3',
          'theme-on-background': '#e6edf3',
        }
      }
    }
  }
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)
app.mount('#app')
