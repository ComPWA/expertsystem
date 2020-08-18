module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "header-max-length": [0, "always", 43],
    "type-enum": [
      2,
      "always",
      [
        "build",
        "ci",
        "chore",
        "docs",
        "feat",
        "fix",
        "refactor",
        "style",
        "test",
      ],
    ],
  },
};
