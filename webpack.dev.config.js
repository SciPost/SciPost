var webpack = require("webpack");
var BundleTracker = require('webpack-bundle-tracker');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
var glob = require("glob");
var path_bundles = __dirname + '/static_bundles/bundles';

module.exports = {
    mode: 'development',
    context: __dirname,
    entry: {
        main: [
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
    module: {
        // loaders: [
        //     {
        //         test: /\.css$/,
        //         // loader: ExtractTextPlugin.extract({
        //         //     fallback: "style-loader",
        //         //     use: "css-loader",
        //         // })
	// 	use: [MiniCssExtractPlugin.loader, 'css-loader'],
        //     },
        //     {
        //         test: /\.less$/,
        //         // loader: ExtractTextPlugin.extract({
        //         //     fallback: "style-loader",
        //         //     use: "css-loader!less-loader"
        //         // })
	// 	use: [MiniCssExtractPlugin.loader, 'css-loader!less-loader'],
        //     },
        //     {
        //         test: /\.scss$/,
        //         // loader: ExtractTextPlugin.extract({
        //         //     fallback: "style-loader",
        //         //     use: "css-loader!sass-loader"
        //         // })
	// 	use: [MiniCssExtractPlugin.loader, 'css-loader!sass-loader'],
        //     }
        // ],
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
	    	use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader'],
            },
            // {
            //     test: /\.less$/,
	    // 	use: [MiniCssExtractPlugin.loader, 'less-loader'],
            // },
            {
                test: /\.scss$/,
	    	use: [MiniCssExtractPlugin.loader, 'sass-loader'],
            }
	]
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            Tether: 'tether',
            'window.Tether': 'tether',
            Tooltip: "exports-loader?Tooltip!bootstrap/js/dist/tooltip",
            Util: 'exports-loader?Util!bootstrap/js/dist/util',
            Popper: ['popper.js', 'default'],
        }),
        new BundleTracker({
            filename: './webpack-stats.json'
        }),
	new MiniCssExtractPlugin({
            filename: 'css/[name]-[hash].css',
        }),
        new CleanWebpackPlugin(
	    // ['css', 'js'], {
            // root: path_bundles,
            // dry: false,
            // exclude: []
            // }
	),
        // new webpack.optimize.UglifyJsPlugin(),
        new webpack.optimize.OccurrenceOrderPlugin(),
        new webpack.optimize.AggressiveMergingPlugin()
    ],
}
