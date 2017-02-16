module.exports = {
    entry: './static/app.js',
    output: {
        filename: './static/bundle.js'
    },
    module: {
        loaders: [
            { test: /\.js$/, exclude: /node_modules/, loader: "babel-loader" }
        ]
    }
}
module: {
}
