import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { globalIgnores } from "eslint/config";
import { defineConfig } from "eslint/config";
import eslintImportPlugin from "eslint-plugin-import";
import reactX from "eslint-plugin-react-x";
import reactDom from "eslint-plugin-react-dom";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";
import pluginRouter from "@tanstack/eslint-plugin-router";

export default defineConfig([
  globalIgnores([
    "dist",
    "**/components/ui",
    "**/components/mode-toggle.tsx",
    "**/components/theme-provider.tsx",
  ]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      // tseslint.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      //...tseslint.configs.strictTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
      reactX.configs["recommended-typescript"],
      reactDom.configs.recommended,
      eslintImportPlugin.flatConfigs.recommended,
      eslintImportPlugin.flatConfigs.typescript,
      ...pluginRouter.configs["flat/recommended"],
    ],
    rules: {
      "import/no-unresolved": "error",
      "sort-imports": [
        "error",
        {
          ignoreCase: false,
          ignoreDeclarationSort: true, // don"t want to sort import lines, use eslint-plugin-import instead
          ignoreMemberSort: false,
          memberSyntaxSortOrder: ["none", "all", "multiple", "single"],
          allowSeparatedGroups: true,
        },
      ],
      "import/order": [
        "error",
        {
          groups: [
            "builtin",
            "external",
            "internal",
            ["sibling", "parent", "index"],
            "unknown",
          ],
          "newlines-between": "always",
          alphabetize: {
            order: "asc",
            caseInsensitive: true,
          },
        },
      ],
    },
    settings: {
      "import/resolver": {
        typescript: {
          project: "./tsconfig.json",
        },
      },
    },
    languageOptions: {
      parserOptions: {
        project: ["./tsconfig.node.json", "./tsconfig.app.json"],
        tsconfigRootDir: import.meta.dirname,
      },
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
  eslintPluginPrettierRecommended,
]);
