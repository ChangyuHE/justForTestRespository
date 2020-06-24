import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Import from '../views/Import.vue'
import Search from '../views/Search.vue'

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

export default router
