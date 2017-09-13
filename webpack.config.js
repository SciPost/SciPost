var webpack = require("webpack");
var BundleTracker = require('webpack-bundle-tracker');
var CleanWebpackPlugin = require('clean-webpack-plugin');
var ExtractTextPlugin = require("extract-text-webpack-plugin");
var glob = require("glob");
var path_bundles = __dirname + '/static_bundles/bundles';

module.exports = {
    context: __dirname,
    entry: {
        main: [
            "bootstrap-loader",
            "./scipost/static/scipost/assets/js/scripts.js",
        ],
        homepage: [
            "./scipost/static/scipost/assets/js/newsticker.js",
        ],
    },
    output: {
        path: path_bundles,
        publicPath: '/static/bundles/',
        filename: "js/[name]-[hash].js",
    },
    module: {
        loaders: [
            {
                test: /\.css$/,
                loader: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader",
                })
            },
            {
                test: /\.less$/,
                loader: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader!less-loader"
                })
            },
            {
                test: /\.scss$/,
                loader: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader!sass-loader"
                })
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            Tether: 'tether',
            'window.Tether': 'tether',
            // Alert: 'exports-loader?Alert!bootstrap/js/dist/alert',
            // Button: 'exports-loader?Button!bootstrap/js/dist/button',
            // Carousel: 'exports-loader?Carousel!bootstrap/js/dist/carousel',
            // Collapse: 'exports-loader?Collapse!bootstrap/js/dist/collapse',
            // Dropdown: 'exports-loader?Dropdown!bootstrap/js/dist/dropdown',
            // Modal: 'exports-loader?Modal!bootstrap/js/dist/modal',
            // Popover: 'exports-loader?Popover!bootstrap/js/dist/popover',
            // Scrollspy: 'exports-loader?Scrollspy!bootstrap/js/dist/scrollspy',
            // Tab: 'exports-loader?Tab!bootstrap/js/dist/tab',
            Tooltip: "exports-loader?Tooltip!bootstrap/js/dist/tooltip",
            Util: 'exports-loader?Util!bootstrap/js/dist/util',
            Popper: ['popper.js', 'default'],
        }),
        new BundleTracker({
            filename: './webpack-stats.json'
        }),
        new ExtractTextPlugin({
            filename: 'css/[name]-[hash].css',
        }),
        new CleanWebpackPlugin(['css', 'js'], {
            root: path_bundles,
            dry: false,
            exclude: []
        }),
        // new webpack.optimize.UglifyJsPlugin(),
        // new webpack.optimize.OccurrenceOrderPlugin(),
        // new webpack.optimize.AggressiveMergingPlugin()
    ],
}
