const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Fix pnpm hoisting issue with expo-modules-core
config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];

config.resolver.extraNodeModules = new Proxy(
  {},
  {
    get: (target, name) => {
      if (typeof name !== 'string') return undefined;
      // Try to resolve from the project root first
      try {
        return path.dirname(require.resolve(name + '/package.json', { paths: [__dirname] }));
      } catch {
        return path.join(__dirname, `node_modules/${name}`);
      }
    },
  }
);

module.exports = config;
