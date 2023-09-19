const path = require("path");
const webpack = require("webpack");

module.exports = {
  entry: {
    main: "./assets/index.js",
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "./static/dist"),
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        options: { presets: ["@babel/preset-env", "@babel/preset-react"] },
      },
    ],
  },
  mode: "development",
  plugins: [
    new webpack.DefinePlugin({
      "process.env": {
        NODE_ENV: JSON.stringify("development"),
      },
    }),
  ],
};
