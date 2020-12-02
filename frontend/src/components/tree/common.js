export function isIDsFilter(name) {
    return ['user', 'gen', 'os', 'os_group', 'platform', 'component', 'feature'].includes(name)
}

export function filterItemText(model) {
        if (model == 'platform') {
            return 'short_name'
        }
        return 'name'
}

// get branch as list of nodes starting from leaf
export function getBranchForLeaf(node) {
    let branch = [node]
    if (node.$children.length == 0) {   // is leaf
        while (node.$parent.model !== undefined) {      // is root
            node = node.$parent
            branch.push(node)
        }
    }
    return branch
}
