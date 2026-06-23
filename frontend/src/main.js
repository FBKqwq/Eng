import { createApp } from 'vue'
import Particles from '@tsparticles/vue3'
import { loadSlim } from '@tsparticles/slim'
import App from './App.vue'
import router from './router'
import './assets/styles/index.css'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

createApp(App)
  .use(router)
  .use(Particles, {
    init: async (engine) => {
      await loadSlim(engine)
    }
  })
  .mount('#app')
