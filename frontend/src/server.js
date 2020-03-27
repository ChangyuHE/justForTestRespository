import axios from 'axios';

const instance = axios.create({
    baseURL:
        process.env.NODE_ENV !== 'production' ?
            process.env.VUE_APP_API_BASE_URL + ':' + process.env.VUE_APP_API_PORT :
                process.env.VUE_APP_API_BASE_URL
});
console.log(instance.defaults.baseURL);

export default instance;