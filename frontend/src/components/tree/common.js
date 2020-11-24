export function isIDsFilter(name) {
    return ['user', 'gen', 'os', 'os_group', 'platform', 'component', 'feature'].includes(name)
}

export function filterItemText(model) {
        if (model == 'platform') {
            return 'short_name'
        }
        return 'name'
}
