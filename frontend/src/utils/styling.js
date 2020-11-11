/**
 * Temporary add className to row selected by query selector `[${idAttr}="${id}"]`
 * @param {String} id : id to find element to add class to
 * @param {String} className : class to assign
 * @param {String} idAttr : query selector
 */
export function justEditedAnimation(id, className, idAttr) {
    let editedRow = document.querySelector(`[${idAttr}="${id}"]`).closest('tr')
    editedRow.classList.add(className)
    setTimeout(() => editedRow.classList.remove(className), 2000)
}

export function getTextColorFromStatus(s) {
    s = s.toLowerCase()
    if (s === 'passed') {
        return 'green--text text--darken-1'
    } else if (s === 'failed') {
        return 'red--text text--darken-3'
    } else if (s === 'error') {
        return 'purple--text text--darken-1'
    } else if (s === 'blocked') {
        return 'yellow--text text--darken-3'
    } else if (s === 'skipped') {
        return 'grey--text text--darken-1'
    } else if (s === 'canceled') {
        return 'blue--text text--lighten-3'
    }
    return undefined
}

export function getColorFromStatus(s) {
    return s ? `${s.toLowerCase()}_status` : undefined
}