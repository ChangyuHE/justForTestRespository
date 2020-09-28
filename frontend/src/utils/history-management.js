import qs from 'query-string'

function composeQueryString(params) {
    let parsed = qs.parse(location.search, {arrayFormat: 'comma'})
    let merged = Object.assign(parsed, params)
    return qs.stringify(merged, {arrayFormat: 'comma'})
}

export function replaceState(params) {
    history.replaceState(null, null, `?${composeQueryString(params)}`)
}

export function pushState(params) {
    history.pushState(null, null, `?${composeQueryString(params)}`)
}