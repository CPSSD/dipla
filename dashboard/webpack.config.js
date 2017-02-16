module.exports = {
    entry: './static/app.js',
    output: {
        filename: './static/app.compiled.js'
    },
    module: {
        loaders: [
            { test: /\.js$/, exclude: /node_modules/, loader: "babel-loader" }
        ]
    }
}
module: {
}
