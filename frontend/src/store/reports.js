import server from '@/server.js';

export default {
    namespaced: true,
    state: {
        reportLoading: false,
        excelLoading: false,
        showReport: false,
        headers: [],
        items: [],
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
            commit('SET_STATE', {'reportLoading': true});

            await server
                .get(url)
                .then(response => {
                    // console.log(response.data);
                    commit('SET_STATE', {'headers': response.data.headers})
                    commit('SET_STATE', {'items': response.data.items})
                })
                .catch(error => {
                    console.log(error);
                    throw new Error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`);
                })
                .finally(() => {
                    commit('SET_STATE', {'reportLoading': false});
                    commit('SET_STATE', {'showReport': true});
                });
        },
        /**
         * Download Excel report generated on backend based on selected validations ids
         */
        async reportExcel({ commit }, { url }) {
            commit('SET_STATE', {'excelLoading': true});
            console.log(url);

            await server
                .get(url, {responseType: 'blob'})
                .then(response => {
                    let fileName = 'unknown';
                    const contentDisposition = response.headers['content-disposition'];
                    console.log(contentDisposition)
                    if (contentDisposition) {
                        const m = contentDisposition.match(/filename="(.+)"/);
                        if (m.length == 2)
                            fileName = m[1];
                    }
                    const uri = window.URL.createObjectURL(new Blob([response.data]));
                    const link = document.createElement('a');
                    link.href = uri;
                    link.setAttribute('download', fileName);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                })
                .catch(error => {
                    console.log(error);
                    throw new Error(`${error}<br> URL: ${server.defaults.baseURL}/${url}`)
                })
                .finally(() => commit('SET_STATE', {'excelLoading': false}));
        },
    }
}