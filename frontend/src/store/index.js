import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

import tree from './tree'
import reports from './reports'
import server from '@/server'

export default new Vuex.Store({
    modules: {
        tree,
        reports
    },
    state: {
        userData: {username: ''},
        importErrors: {},
    },
    getters: {
        importErrors: (state) => state.importErrors,
        userName: (state) => state.userData.username
    },
    mutations: {
        SET_IMPORT_ERRORS: (state, payload) => state.importErrors = payload,
        DELETE_IMPORT_ERROR: (state, {id, priority, errorCode}) => {
            state.importErrors[priority][errorCode] = state.importErrors[priority][errorCode].filter(e => { return e.ID != id })
            for (const code in state.importErrors[priority]) {
                if (state.importErrors[priority][code].length == 0)
                    Vue.delete(state.importErrors[priority], code)
            }
            for (const priority in state.importErrors) {
                if (Object.keys(state.importErrors[priority]).length == 0)
                    Vue.delete(state.importErrors, priority)
            }
        },
        SET_USER_DATA: (state, payload) => state.userData = payload,
    },
    actions: {
        setImportErrors: ({ commit }, payload) => {
            commit('SET_IMPORT_ERRORS', payload)
        },
        deleteImportError: ({ commit }, payload) => {
            commit('DELETE_IMPORT_ERROR', payload)
        },
        getUserData: ({ commit }) => {
            const url = 'api/users/current/'
            return server
                .get(url)
                .then(response => {
                    commit('SET_USER_DATA', response.data)
                })
                .catch(error => {
                    error.handleGlobally('Could not get current user data', url)
                })
        }
    },
    strict: process.env.NODE_ENV !== 'production'
});
