/**
 * Vue Router Configuration - Experiment Versioning Dashboard
 */

import { createRouter, createWebHistory } from 'vue-router'
import ExperimentView from '../views/ExperimentView.vue'

const routes = [
  {
    path: '/',
    redirect: '/experiments',
  },
  {
    path: '/experiments',
    name: 'Experiments',
    component: ExperimentView,
    meta: {
      title: 'Experiment Lineage',
      icon: '🔬',
    },
  },
  {
    path: '/experiments/:experimentId',
    name: 'ExperimentDetail',
    component: ExperimentView,
    meta: {
      title: 'Experiment Detail',
      icon: '🔬',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/experiments',
  },
]

const router = createRouter({
  history: createWebHistory(),
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
