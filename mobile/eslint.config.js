// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ["dist/*"],
  },
  {
    rules: {
      // Fetch-on-mount (useEffect + setState) is the standard data-loading
      // pattern used throughout this app's hooks/contexts; don't error on it.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
]);
