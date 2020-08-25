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