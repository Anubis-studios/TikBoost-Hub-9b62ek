const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const fs = require('fs');

const config = getDefaultConfig(__dirname);

config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];

/**
 * Fix pnpm hoisting issue: the hoisted `.pnpm/node_modules/expo-modules-core`
 * doesn't contain build artifacts. We scan the pnpm store to find the real
 * package that actually has `build/index.js`.
 */
function findPnpmPackageWithBuild(packageName) {
  const pnpmDir = path.join(__dirname, 'node_modules/.pnpm');
  if (!fs.existsSync(pnpmDir)) return null;

  // Normalise scoped packages: @expo/vector-icons -> @expo+vector-icons
  const dirPrefix = packageName.replace(/\//g, '+').replace(/^@/, '');

  let entries;
  try {
    entries = fs.readdirSync(pnpmDir);
  } catch {
    return null;
  }

  for (const entry of entries) {
    if (!entry.startsWith(dirPrefix)) continue;
    const pkgPath = path.join(pnpmDir, entry, 'node_modules', packageName);
    const buildEntry = path.join(pkgPath, 'build', 'index.js');
    if (fs.existsSync(buildEntry)) {
      return buildEntry;
    }
    const rootIndex = path.join(pkgPath, 'index.js');
    if (fs.existsSync(rootIndex)) {
      return rootIndex;
    }
  }
  return null;
}

const expoModulesCoreEntry = findPnpmPackageWithBuild('expo-modules-core');

if (expoModulesCoreEntry) {
  config.resolver.extraNodeModules = {
    ...(config.resolver.extraNodeModules || {}),
    'expo-modules-core': expoModulesCoreEntry,
  };
}

module.exports = config;
