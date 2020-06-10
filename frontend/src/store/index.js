import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

let store = new Vuex.Store({
    state: {
        validations: [],
        branches: [],
        treeLoading: true,

        importErrors: {},
    },
    getters: {
        importErrors: (state) => state.importErrors,
    },
    mutations: {
        SET_SELECTED(state, { validations, branches }) {
            state.branches = branches;
            state.validations = validations;
        },
        SET_TREE_LOADING: (state, status) =>  state.treeLoading = status,
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
        }
    },
    actions: {
        // validations tree
        setTreeLoading: ({ commit }, payload) => {
            commit('SET_TREE_LOADING', payload);
        },
        setSelected: ({ commit }, payload) => {
            commit('SET_SELECTED', payload);
        },
        // import errors
        setImportErrors: ({ commit }, payload) => {
            commit('SET_IMPORT_ERRORS', payload);
        },
        deleteImportError: ({ commit }, payload) => {
            commit('DELETE_IMPORT_ERROR', payload);
        },
    },
    modules: {
    },
    strict: process.env.NODE_ENV !== 'production'
});

export default store;