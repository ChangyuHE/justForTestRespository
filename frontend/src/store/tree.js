import _ from 'lodash'
import { getTextColorFromStatus } from '@/utils/styling.js'

export default {
    namespaced: true,
    state: {
        validations: [],
        limbs: [],
        treeLoading: true,
    },
    getters: {
        branches: state => state.limbs.map(lst => {
            let statuses = ''
            for (const status of ['passed', 'failed', 'error', 'blocked', 'skipped', 'canceled']) {
                const cls = getTextColorFromStatus(status)
                statuses += `<span class='${cls} gta_status' title='${_.upperFirst(status)}'>${lst[6][status]}</span>`
            }
            const firstLine = `${statuses}${lst[6].text} (${lst[2]}, ${lst[4]}, ${lst[5]})`
            const secondLine = `<span class='grey--text text--lighten-1'>at ${lst[6].date} by ${lst[6].owner}</span>`
            return firstLine + '<br/>' + secondLine
        })
    },
    mutations: {
        SET_SELECTED(state, { validations, branches }) {
            state.limbs = branches
            state.validations = validations
        },
        ADD_SELECTED(state, { validations, branches }) {
            state.validations = _.union(state.validations, validations)
            branches.forEach(b => {
                if (_.findIndex(state.limbs, limb => _.isMatch(limb, b)) == -1) {
                    state.limbs.push(b)
                }
            })
        },
        REMOVE_SELECTED(state, { validations, branches }) {
            state.validations = _.differenceWith(state.validations, validations, _.isEqual)

            branches.forEach(b => {
                let index = _.findIndex(state.limbs, limb => _.isMatch(limb, b))
                if (index !== -1) {
                    state.limbs.splice(index, 1)
                }
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
        removeSelected: ({ commit }, payload) => {
            commit('REMOVE_SELECTED', payload)
        },
        setTreeLoading: ({ commit }, payload) => {
            commit('SET_TREE_LOADING', payload)
        }
    }
}
