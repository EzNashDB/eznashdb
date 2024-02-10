const path = require("path");
const webpack = require("webpack");
const glob = require("glob");

const entry = {};
const entryFiles = glob.sync("./assets/entryPoints/**/*.js");

entryFiles.forEach((file) => {
  const entryName = path.basename(file, path.extname(file));
  entry[`./${entryName}`] = `./${file}`;
});

module.exports = {
  entry: entry,
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
      {
        test: /\.(sass|less|css)$/,
        use: ["style-loader", "css-loader", "less-loader"],
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg)$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "[name].[ext]",
              outputPath: "images/",
            },
          },
        ],
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
