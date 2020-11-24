const BundleTracker = require("webpack-bundle-tracker");

let publicPathUrl = '', publicApiPathUrl = '';
if (process.env.NODE_ENV !== 'production'){
    publicPathUrl = process.env.VUE_APP_API_BASE_URL + ':' + process.env.PORT;
    publicApiPathUrl = process.env.VUE_APP_API_BASE_URL + ':' + process.env.VUE_APP_API_PORT;
} else {
    publicPathUrl = process.env.VUE_APP_API_BASE_URL;
    publicApiPathUrl = process.env.VUE_APP_API_BASE_URL;
}

module.exports = {
    publicPath: publicPathUrl,
    outputDir: './dist/',
    assetsDir: 'static',

    devServer: {
        historyApiFallback: true,
        proxy: {
            '/api/results/v1': {
                target: 'https://gta.intel.com/',
                'changeOrigin': true,
                'secure': false
            }
        }
    },
    chainWebpack: config => {
        config.optimization
            .splitChunks(false)

        config
            .plugin('BundleTracker')
            .use(BundleTracker, [{filename: './webpack-stats.json'}])

        config.resolve.alias
            .set('__STATIC__', 'static')

        config.devServer
            .public(publicPathUrl)
            .host('127.0.0.1')
            .port(8080)
            .hotOnly(true)
            .watchOptions({poll: 1000})
            .https(false)
            .headers({"Access-Control-Allow-Origin": ["\*"]})
    }
};