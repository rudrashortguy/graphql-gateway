import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  { ignores: ["dist"] },
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: { ecmaVersion: "latest", sourceType: "module", parserOptions: { ecmaFeatures: { jsx: true } }, globals: { ...globals.browser, ...globals.es2021 } },
    rules: { "no-unused-vars": "off", "no-undef": "warn" },
  },
];
