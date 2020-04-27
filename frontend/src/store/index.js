import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

let store = new Vuex.Store({
    state: {
        validations: [],
        branches: [],
        treeLoading: true,

    },
    getters: {
        
    },
    mutations: {
        setSelected(state, { validations, branches }) {
            state.branches = branches;
            state.validations = validations;
        },
        setTreeLoading: (state, status) =>  state.treeLoading = status,
    },
    actions: {
        
    },
    modules: {
    },
    strict: process.env.NODE_ENV !== 'production'
});

export default store;