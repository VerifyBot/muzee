/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

// Plugins
import { registerPlugins } from '@/plugins'

const app = createApp(App)

import { MuzeeAPI } from './api.js'

app.config.globalProperties.api = new MuzeeAPI();
window.api = app.config.globalProperties.api;

registerPlugins(app)

app.mount('#app')
