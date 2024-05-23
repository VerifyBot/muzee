// Composables
import { createRouter, createWebHistory } from "vue-router";
import { defineAsyncComponent } from "vue";

import Home from "@/views/Home.vue"
import LoginRedirector from "@/views/LoginRedirector.vue"
import Default from "@/layouts/default/Default.vue"

const routes = [
  {
    path: "/login",
    component: LoginRedirector,
  },
  {
    path: "/",
    component: Default,
    children: [
      {
        path: "",
        name: "Home",
        // route level code-splitting
        // this generates a separate chunk (about.[hash].js) for this route
        // which is lazy-loaded when the route is visited.
        component: Home,
      },
    ],
  },

];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
