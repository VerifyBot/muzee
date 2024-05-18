/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'
// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          background: '#31072a',
          surface: '#55184d',
          primary: '#da4b8e',
          'primary-darken-1': '#6D214F',
          secondary: '#D6A2E8',
          'secondary-darken-1': '#82589F',
          warning: '#f89b5b',
        },
      },
    },
  },
})
