export default {
    namespaced: true,
    state: {
        validations: [],
        branches: [],
        treeLoading: true,
    },
    getters: {
    },
    mutations: {
        SET_SELECTED(state, { validations, branches }) {
            state.branches = branches;
            state.validations = validations;
        },
        SET_TREE_LOADING: (state, status) =>  state.treeLoading = status,
    },
    actions: {
        setSelected: ({ commit }, payload) => {
            commit('SET_SELECTED', payload);
        },
        setTreeLoading: ({ commit }, payload) => {
            commit('SET_TREE_LOADING', payload);
        },
    }
}