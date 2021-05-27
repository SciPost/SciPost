var webpack = require("webpack");
var BundleTracker = require('webpack-bundle-tracker');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const { VueLoaderPlugin } = require('vue-loader')
var path_bundles = __dirname + '/static_bundles/bundles';

module.exports = {
    mode: 'development',
    context: __dirname,
    devtool: "source-map", // to ensure no eval() (breaking CSP) in development
    entry: {
        base: [
	    // "tether",
            // "bootstrap-loader",
            // "./scipost_django/scipost/static/scipost/assets/js/scripts.js",
            "./scipost_django/scipost/static/scipost/assets/js/base.js",
        ],
        // homepage: [
        //     "./scipost_django/scipost/static/scipost/assets/js/fader.js",
        //     "./scipost_django/scipost/static/scipost/assets/js/newsticker.js",
        // ],
	// apimail: [
        //     "./scipost_django/apimail/static/apimail/assets/vue/messages_table.js",
	// ],
	qr: [
	    "./scipost_django/scipost/static/scipost/assets/js/activate_qr.js",
	],
    },
    output: {
        path: path_bundles,
        publicPath: '/static/bundles/',
        filename: "js/[name]-[hash].js",
    },
    module: {
	rules: [
	    // {
	    // 	test: require.resolve('jquery'),
	    // 	use: [
	    // 	    {
	    // 		loader: 'expose-loader',
	    // 		options: 'jQuery'
	    // 	    },
	    // 	    {
	    // 		loader: 'expose-loader',
	    // 		options: '$'
	    // 	    }
	    // 	]
	    // },
            // {
            //     test: /\.css$/,
	    // 	use: [
	    // 	    'vue-style-loader',
	    // 	    'style-loader',
	    // 	    'css-loader',
	    // 	    'postcss-loader'
	    // 	],
            // },
            {
                test: /\.(scss|css)$/,
	    	use: [
		    // 'vue-style-loader',
		    'style-loader',
		    'css-loader',
		    {
			loader: 'postcss-loader',
			options: {
			    postcssOptions: {
				plugins: function() {
				    return [
					require('autoprefixer')
				    ];
				}
			    }
			}
		    },
		    'sass-loader'
		],
            },
	    {
		test: /\.vue$/,
		loader: 'vue-loader'
	    },
	    // {
	    // 	test: /\.js$/,
	    // 	loader: 'babel-loader'
	    // },
	]
    },
    plugins: [
	new BundleTracker({
	    filename: './webpack-stats.json'
	}),
        // new webpack.ProvidePlugin({
        //     // $: 'jquery',
        //     // jQuery: 'jquery',
	//     // 'window.jQuery': 'jquery',
        //     // Tether: 'tether',
        //     // 'window.Tether': 'tether',
        //     Popper: ['popper.js', 'default'],
	//     Alert: "exports-loader?Alert!bootstrap/js/dist/alert",
	//     Button: "exports-loader?Button!bootstrap/js/dist/button",
	//     Carousel: "exports-loader?Carousel!bootstrap/js/dist/carousel",
	//     Collapse: "exports-loader?Collapse!bootstrap/js/dist/collapse",
	//     Dropdown: "exports-loader?Dropdown!bootstrap/js/dist/dropdown",
	//     Modal: "exports-loader?Modal!bootstrap/js/dist/modal",
	//     Popover: "exports-loader?Popover!bootstrap/js/dist/popover",
	//     Scrollspy: "exports-loader?Scrollspy!bootstrap/js/dist/scrollspy",
	//     Tab: "exports-loader?Tab!bootstrap/js/dist/tab",
        //     Tooltip: "exports-loader?Tooltip!bootstrap/js/dist/tooltip",
        //     Util: 'exports-loader?Util!bootstrap/js/dist/util',
        // }),
        new CleanWebpackPlugin(),
        new webpack.optimize.AggressiveMergingPlugin(),
	new VueLoaderPlugin()
    ],
    resolve: {
	alias: {
	    // If using the runtime only build
	    'vue$': 'vue/dist/vue.runtime.esm.js'
	    // Or if using full build of Vue (runtime + compiler) # NOT GOOD WITH CSP
	    // 'vue$': 'vue/dist/vue.esm.js'
	}
    },
    optimization: {
	splitChunks: {
	    chunks: 'all',
	},
    },
}
