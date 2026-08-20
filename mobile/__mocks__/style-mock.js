// jest-expo cannot parse CSS, and theme.ts imports global.css for its web
// build. The tests only care about the exported colour helpers, so the
// stylesheet is stubbed out.
module.exports = {};
