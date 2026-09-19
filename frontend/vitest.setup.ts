import "@testing-library/jest-dom";

process.env.NEXT_PUBLIC_SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://qtcncebuochelpgwqthx.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-anon-key";

// Polyfill window.HTMLElement.prototype.scrollIntoView for jsdom environment
if (typeof window !== "undefined") {
  window.HTMLElement.prototype.scrollIntoView = () => {};
}
