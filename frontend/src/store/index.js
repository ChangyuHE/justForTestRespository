import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

import tree from './tree'
import reports from './reports'
import { request } from './request'
import server from '@/server'

export default new Vuex.Store({
    modules: {
        tree,
        reports,
        request,
    },
    state: {
        userData: {username: ''},
        importErrors: {},
        urlParams: {}
    },
    getters: {
        importErrors: state => state.importErrors,
        userName: state => state.userData.username,
        activeProfile: state => state.userData.profiles.find(p => p.active === true)
    },
    mutations: {
        DELETE_IMPORT_ERROR: (state, {id, priority, errorCode, model}) => {
            state.importErrors[priority][errorCode][model] =
                state.importErrors[priority][errorCode][model].filter(e => e.ID != id)
        },
        DELETE_IMPORT_ERRORS_GROUP: (state, {priority, errorCode, model}) => {
            Vue.delete(state.importErrors[priority][errorCode], model)
        },
        CLEAR_EMPTY_KEYS: (state, {priority}) => {
            for (const code in state.importErrors[priority]) {
                if (Object.keys(state.importErrors[priority][code]).length == 0)
                    Vue.delete(state.importErrors[priority], code)
            }
            for (const priority in state.importErrors) {
                if (Object.keys(state.importErrors[priority]).length == 0)
                    Vue.delete(state.importErrors, priority)
            }
        },
        SET_STATE: (state, payload) => Object.assign(state, payload)
    },
    actions: {
        setImportErrors: ({ commit }, payload) => {
            commit('SET_STATE', {importErrors: payload})
        },
        deleteImportError: ({ commit }, payload) => {
            commit('DELETE_IMPORT_ERROR', payload)
            commit('CLEAR_EMPTY_KEYS', payload)
        },
        deleteImportErrorsGroup: ({ commit }, payload) => {
            commit('DELETE_IMPORT_ERRORS_GROUP', payload)
            commit('CLEAR_EMPTY_KEYS', payload)
        },
        getUserData: ({ commit }) => {
            const url = 'api/users/current/'
            return server
                .get(url)
                .then(response => {
                    commit('SET_STATE', {userData: response.data})
                })
                .catch(error => {
                    error.handleGlobally('Could not get current user data', url)
                })
        },
        setUserDataManually: ({ commit }, payload) => {
            commit('SET_STATE', {userData: payload})
        },
        setUrlParams: ({ commit }, payload) => {
            commit('SET_STATE', {urlParams: payload})
        }
    },
    strict: process.env.NODE_ENV !== 'production'
})
