import _ from 'lodash'
import qs from 'query-string'
import store from '../store'

function composeQueryString(params, toDelete) {
    // get query params
    let parsed = qs.parse(location.search, {arrayFormat: 'comma'})
    let initial = {...parsed}
    // merge new and parsed params
    let merged = Object.assign(parsed, params)
    // delete all from toDelete
    toDelete.forEach(p => delete merged[p])

    if (!_.isEqual(initial, merged)) {
        // save url params to store
        store.commit('SET_URL_PARAMS', merged)
        // return value to write to history
        return qs.stringify(merged, {arrayFormat: 'comma'})
    } else {
        return 'no action'
    }
}

export function alterHistory(type, params, toDelete=[]) {
    let func = (type == 'push') ? history.pushState : history.replaceState
    let queryParams = composeQueryString(params, toDelete)
    if (queryParams !== 'no action') {
        func.call(history, null, null, `?${queryParams}`)
    }
}