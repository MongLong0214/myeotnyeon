import { strictEqual } from "node:assert";
import { test } from "node:test";

import { greet } from "../index.js";

test("greet names its argument", () => {
  strictEqual(greet("world"), "hello, world");
});
