import _ from 'lodash'


const fields = {
    component: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
    generation: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
    platform: [
        { label: 'Short name', name: 'short_name', type: 'text' },
        { label: 'Name', name: 'name', type: 'text' },
        { label: 'Aliases (optional)', name: 'aliases', type: 'text' },
        { label: 'Generation', name: 'generation', type: 'autocomplete' }
    ],
    os: [
        { label: 'Name', name: 'name', type: 'text' },
        { label: 'Aliases (optional)', name: 'aliases', type: 'text' },
    ],
    milestone: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
    feature: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
    scenario: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
    env: [
        { label: 'Name', name: 'name', type: 'text' }
    ],
}

const request = {
    namespaced: true,
    state: {
        rules: {
            required: (value, field) => {
                if (_.includes(['name', 'short_name', 'generation'], field))
                    return !!value || 'Required'
                return true
            }
        },
        requestItemDialog: '',
    },
    getters: {
    },
    mutations: {
        SET_REQUEST_DIALOG_STATE(state, modelName) {
            state.requestItemDialog = modelName
        },
    },
    actions: {
        setRequestDialogState: ({ commit }, modelName) => {
            commit('SET_REQUEST_DIALOG_STATE', modelName)
        },
    }
}

export { fields, request }