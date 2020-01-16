var webpack = require("webpack");
var BundleTracker = require('webpack-bundle-tracker');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
var path_bundles = __dirname + '/static_bundles/bundles';

module.exports = {
    mode: 'development',
    context: __dirname,
    devtool: "source-map", // to ensure no eval() (breaking CSP) in development
    entry: {
        main: [
	    "tether",
            "bootstrap-loader",
            "./scipost/static/scipost/assets/js/dynamic_loading.js",
            "./scipost/static/scipost/assets/js/scripts.js",
        ],
        homepage: [
            "./scipost/static/scipost/assets/js/fader.js",
            "./scipost/static/scipost/assets/js/newsticker.js",
        ],
    },
    output: {
        path: path_bundles,
        publicPath: '/static/bundles/',
        filename: "js/[name]-[hash].js",
    },
    plugins: [
	new BundleTracker({
	    filename: './webpack-stats.json'
	}),
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
	    'window.jQuery': 'jquery',
            Tether: 'tether',
            'window.Tether': 'tether',
            Popper: ['popper.js', 'default'],
	    Alert: "exports-loader?Alert!bootstrap/js/dist/alert",
	    Button: "exports-loader?Button!bootstrap/js/dist/button",
	    Carousel: "exports-loader?Carousel!bootstrap/js/dist/carousel",
	    Collapse: "exports-loader?Collapse!bootstrap/js/dist/collapse",
	    Dropdown: "exports-loader?Dropdown!bootstrap/js/dist/dropdown",
	    Modal: "exports-loader?Modal!bootstrap/js/dist/modal",
	    Popover: "exports-loader?Popover!bootstrap/js/dist/popover",
	    Scrollspy: "exports-loader?Scrollspy!bootstrap/js/dist/scrollspy",
	    Tab: "exports-loader?Tab!bootstrap/js/dist/tab",
            Tooltip: "exports-loader?Tooltip!bootstrap/js/dist/tooltip",
            Util: 'exports-loader?Util!bootstrap/js/dist/util',
        }),
        new CleanWebpackPlugin(),
        new webpack.optimize.OccurrenceOrderPlugin(),
        new webpack.optimize.AggressiveMergingPlugin()
    ],
    module: {
	rules: [
	    {
	    	test: require.resolve('jquery'),
	    	use: [{
	    	    loader: 'expose-loader',
	    	    options: 'jQuery'
	    	},{
	    	loader: 'expose-loader',
	    	options: '$'
	    	}]
	    },
            {
                test: /\.css$/,
	    	use: ['style-loader', 'css-loader', 'postcss-loader'],
            },
            {
                test: /\.scss$/,
	    	use: ['style-loader', 'css-loader', 'postcss-loader', 'sass-loader'],
            }
	]
    },
}
