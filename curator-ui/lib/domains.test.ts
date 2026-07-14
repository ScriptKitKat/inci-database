import { describe, expect, it } from "vitest";
import { domainMatches, sourceHostname } from "./domains";

describe("product source domains", () => {
  it("extracts a normalized hostname only from safe HTTPS URLs", () => {
    expect(sourceHostname("https://www.brand.example/products/serum")).toBe("brand.example");
    expect(sourceHostname("http://brand.example/products/serum")).toBeNull();
    expect(sourceHostname("https://user:pass@brand.example/products/serum")).toBeNull();
  });

  it("matches a domain and its subdomains without matching suffix attacks", () => {
    expect(domainMatches("shop.brand.example", "brand.example")).toBe(true);
    expect(domainMatches("brand.example.evil.test", "brand.example")).toBe(false);
  });
});
