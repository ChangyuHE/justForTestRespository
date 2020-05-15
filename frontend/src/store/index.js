import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

let store = new Vuex.Store({
    state: {
        validations: [],
        branches: [],
        treeLoading: true,
        alert: {message: '', type: 'error'}
    },
    getters: {
        
    },
    mutations: {
        setSelected(state, { validations, branches }) {
            state.branches = branches;
            state.validations = validations;
        },
        setTreeLoading: (state, status) =>  state.treeLoading = status,

        setAlert: (state, { message, type }) => {
            message = `Наташа, мы там всё уронили! Вообще всё, Наташ, честно!<br>${message}`;
            state.alert = Object.assign(state.alert, {message, type});
        },
    },
    actions: {
    },
    modules: {
    },
    strict: process.env.NODE_ENV !== 'production'
});

export default store;