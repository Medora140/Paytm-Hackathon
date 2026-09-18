import "@testing-library/jest-dom";

// Polyfill window.HTMLElement.prototype.scrollIntoView for jsdom environment
if (typeof window !== "undefined") {
  window.HTMLElement.prototype.scrollIntoView = () => {};
}
