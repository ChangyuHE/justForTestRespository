import qs from 'query-string'

function composeQueryString(params, toDelete) {
    let parsed = qs.parse(location.search, {arrayFormat: 'comma'})
    let merged = Object.assign(parsed, params)
    toDelete.forEach(p => delete merged[p])
    return qs.stringify(merged, {arrayFormat: 'comma'})
}

export function alterHistory(type, params, toDelete=[]) {
    let func = (type == 'push') ? history.pushState : history.replaceState
    func.call(history, null, null, `?${composeQueryString(params, toDelete)}`)
}