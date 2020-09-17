export default {
    namespaced: true,
    state: {
        validations: [],
        branches: [],
        branchesIds: {},
        treeLoading: true,
    },
    getters: {
    },
    mutations: {
        SET_SELECTED(state, { validations, branches }) {
            state.branches = branches
            state.validations = validations
        },
        REMOVE_FILTERED(state, { validations, branches }) {
            branches.forEach(e => {
                let i = state.branches.indexOf(e)
                if (i !== -1)
                    state.branches.splice(i, 1)
            })
            validations.forEach(e => {
                let i = state.validations.indexOf(e)
                if (i !== -1)
                    state.validations.splice(i, 1)
            })
        },
        ADD_SELECTED(state, { validations, branches }) {
            branches.forEach(e => {
                let i = state.branches.indexOf(e)
                if (i == -1)
                    state.branches.push(e)
            })
            validations.forEach(e => {
                let i = state.validations.indexOf(e)
                if (i == -1)
                    state.validations.push(e)
            })
        },
        SET_TREE_LOADING: (state, status) =>  state.treeLoading = status,
    },
    actions: {
        setSelected: ({ commit }, payload) => {
            commit('SET_SELECTED', payload)
        },
        addSelected: ({ commit }, payload) => {
            commit('ADD_SELECTED', payload)
        },
        removeFiltered: ({ commit }, payload) => {
            commit('REMOVE_FILTERED', payload)
        },
        setTreeLoading: ({ commit }, payload) => {
            commit('SET_TREE_LOADING', payload)
        },
    }
}