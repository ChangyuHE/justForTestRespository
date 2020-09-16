import server from '@/server.js'

export default {
    namespaced: true,
    state: {
        reportLoading: false,
        excelLoading: false,
        showReport: false,
        originalHeaders: [],
        originalItems: [],
    },
    getters: {
    },
    mutations: {
        SET_STATE: (state, payload) => Object.assign(state, payload)
    },
    actions: {
        /**
         * Get report data from backend based on selected validations ids
         */
        async reportWeb({ commit }, { url }) {
            commit('SET_STATE', {'reportLoading': true})

            await server
                .get(url)
                .then(response => {
                    commit('SET_STATE', {'originalHeaders': response.data.headers})
                    commit('SET_STATE', {'originalItems': response.data.items})
                })
                .catch(error => {
                    throw error
                })
                .finally(() => {
                    commit('SET_STATE', {'reportLoading': false})
                    commit('SET_STATE', {'showReport': true})
                })
        },
        /**
         * Download Excel report generated on backend based on selected validations ids
         */
        async reportExcel({ commit }, { url }) {
            commit('SET_STATE', {'excelLoading': true})

            await server
                .get(url, {responseType: 'blob'})
                .then(response => {
                    let fileName = 'unknown'
                    const contentDisposition = response.headers['content-disposition']
                    console.log(contentDisposition)
                    if (contentDisposition) {
                        const m = contentDisposition.match(/filename="(.+)"/)
                        if (m.length == 2)
                            fileName = m[1]
                    }
                    const link = document.createElement('a')
                    link.href = window.URL.createObjectURL(new Blob([response.data]))
                    link.setAttribute('download', fileName)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                })
                .catch(error => {
                    throw error
                })
                .finally(() => commit('SET_STATE', {'excelLoading': false}))
        },
    }
}