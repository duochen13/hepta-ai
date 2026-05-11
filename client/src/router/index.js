/**
 * Vue Router Configuration - Experiment Versioning Dashboard
 * Base path: /playground/
 */

import { createRouter, createWebHistory } from 'vue-router'
import ExperimentView from '../views/ExperimentView.vue'

const routes = [
  {
    path: '/',
    name: 'Playground',
    component: ExperimentView,
    meta: {
      title: 'Experiment Lineage',
      icon: '🔬',
    },
  },
  {
    path: '/:experimentId',
    name: 'PlaygroundDetail',
    component: ExperimentView,
    meta: {
      title: 'Experiment Detail',
      icon: '🔬',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory('/playground/'),
  routes,
})

// Update document title on route change
router.beforeEach((to, from, next) => {
  document.title = to.meta.title
    ? `${to.meta.title} - DataVint`
    : 'DataVint - Experiment Versioning'
  next()
})

export default router
