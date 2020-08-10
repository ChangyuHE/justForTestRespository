import Vue from 'vue'
import VueRouter from 'vue-router'
import store from '@/store'

import Home from '../views/Home'
import Import from '../views/Import'
import Search from '../views/Search'
import TestVerifier from '../views/TestVerifier'

Vue.use(VueRouter)

const routes = [
    {
        path: '/',
        alias: '/Validations',
        name: 'home',
        component: Home
    },
    {
        path: '/import',
        name: 'import',
        component: Import
    },
    {
        path: '/search',
        name: 'search',
        component: Search
    },
    {
        path: '/test-verifier',
        name: 'test-verifier',
        component: TestVerifier
    },
    {
        path: '/feature-mapping',
        name: 'feature-mapping',
        component: () => import(/* webpackChunkName: "FMT" */ '../views/FeatureMapping/Show.vue')
        // component: FeatureMapping
    },
    // {
    //     path: '/about',
    //     name: 'About',
    //     // route level code-splitting
    //     // this generates a separate chunk (about.[hash].js) for this route
    //     // which is lazy-loaded when the route is visited.
    //     component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
    // }
]

const router = new VueRouter({
    mode: 'history',
    // base: process.env.BASE_URL,
    base: '/',
    // linkExactActiveClass: "router-active-exact",
    // linkActiveClass: "router-active",
    routes
})

// Navigation guard to get user data first
const storeInit = store.dispatch('getUserData')
router.beforeEach((to, from, next) => {
    storeInit
        .then(next)
        .catch(error => {
            error.handleGlobally && error.handleGlobally('Error during initial data loading', url)
        })
  })

export default router
