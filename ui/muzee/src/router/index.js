// Composables
import { createRouter, createWebHistory } from "vue-router";
import { defineAsyncComponent } from "vue";

const routes = [
  {
    path: "/login",
    component: () => defineAsyncComponent(() => import("@/views/LoginRedirector.vue")),
  },
  {
    path: "/",
    component: () => defineAsyncComponent(() => import("@/layouts/default/Default.vue")),
    children: [
      {
        path: "",
        name: "Home",
        // route level code-splitting
        // this generates a separate chunk (about.[hash].js) for this route
        // which is lazy-loaded when the route is visited.
        component: () =>
        defineAsyncComponent(() => import("@/views/Home.vue")),
      },
    ],
  },

];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
