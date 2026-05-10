import assert from "node:assert";
import { describe, it } from "node:test";
import { createNdjsonParser } from "./parser.js";

describe("createNdjsonParser", () => {
  it("parses a single complete line", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push('{"n":1}\n'), [{ n: 1 }]);
  });

  it("ignores empty lines", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push("\n\n{\"z\":0}\n\n"), [{ z: 0 }]);
  });

  it("buffers until a newline completes a line", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push('{"a":'), []);
    assert.deepStrictEqual(p.push('true}\n'), [{ a: true }]);
  });

  it("splits records across chunk boundaries", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push('{"x":1}\n{"y":'), [{ x: 1 }]);
    assert.deepStrictEqual(p.push('2}\n'), [{ y: 2 }]);
  });

  it("flush drains full lines without new data", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push("{\"k\":\"v\"}\n{\"pending\":"), [{ k: "v" }]);
    assert.deepStrictEqual(p.flush(), []);
    assert.deepStrictEqual(p.push("1}\n"), [{ pending: 1 }]);
  });

  it("leaves a trailing partial line in the buffer", () => {
    const p = createNdjsonParser();
    assert.deepStrictEqual(p.push('{"only":"partial"'), []);
    assert.deepStrictEqual(p.flush(), []);
  });
});
