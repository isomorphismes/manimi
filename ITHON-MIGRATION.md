# Manimi Ithon migration

The destination is an Ithon implementation of the engine, not Python files
with different punctuation.

At the start of the migration, the repository contains 114 Python files and
27,584 Python lines. The engine itself is 100 modules and 25,133 lines, with
275 classes, 1,864 functions or methods, 362 uses of variadic parameters, and
1,018 attribute-assignment targets. It is the WebGPU/WGSL engine: the 20 WGSL
shader files and their buffer, binding, and layout contracts remain part of
the implementation.

## Language boundary

- `.pi` is Ithon source. It uses `∈`/`∋` for typing and membership and is
  parsed and checked in full before execution.
- `.py` is foreign Python. A retained `.py` counterpart is a compatibility
  path, not evidence that its `.pi` counterpart ran.
- `./bin/manimi` enters through Ithon. `manimgl` remains the foreign-Python
  command during migration.
- Manimi's file loader uses Ithon's source loader for `.pi` scenes, so scene
  files receive the same whole-module check as imported Ithon modules.
- The converted leaf modules are `manimlib/utils/rate_functions.pi` and
  `manimlib/utils/images.pi`. Their `.py` counterparts remain temporarily for
  Python compatibility; Ithon's finder gives the `.pi` modules priority.

## Foreign facilities

Ithon owns the syntax and whole-module checks for `.pi` files. The current host
runtime still executes the checked lowering on CPython. NumPy, Pillow, wgpu-py,
ManimPango, and their compiled dependencies remain explicit foreign libraries;
Ithon checks their use at the import boundary, not their implementations. WGSL
is likewise a renderer boundary: the checked render receipt requires successful
WebGPU device creation and shader-module compilation, but does not claim that
Ithon type-checks WGSL.

The retained `.py` modules are loaded only as explicit compatibility references
in parity tests. Those tests load the `.pi` side through
`IthonSourceLoader`; manually lowering or rewriting a `.pi` file in a test does
not count as checked execution.

## Ordered conversion

1. Establish the checked launcher, `.pi` scene loading, packaging, and tests.
2. Convert deterministic leaf utilities and verify numerical parity.
3. Type the WebGPU data layouts, buffers, shader bindings, and renderer core
   without changing the WGSL interface.
4. Convert mobjects, cameras, animations, and scenes in dependency order.
5. Convert the remaining command, reload, and interactive paths.
6. Remove each Python counterpart only after its Ithon replacement passes the
   same behavior and render comparisons.

This order deliberately keeps the WebGPU work already on `master`; the rewrite
does not revert to the older OpenGL architecture described by some stale docs.

## Gates

Every converted module must have:

- a native Ithon parse and mandatory static check;
- a behavior comparison with the Python implementation while that reference
  exists;
- render or buffer-layout comparison when the module affects pixels or GPU
  data;
- no implicit `Any`, unchecked star import, or silent Python fallback.

Ithon can run its checked frontend on the same installed Python as Manimi's
compiled dependencies. `./bin/manimi` sets that interpreter explicitly and
keeps the checked `.pi` entry point, `.pi` importer, and renderer in one
process. Native CPython builds remain useful for testing Ithon's tokenizer and
grammar, but are no longer an ABI gate for rendering Manimi.

## Ithon dependency

The required Ithon work landed on `main` through Ithon PRs #2 and #5. It adds
the smallest non-dynamic support demanded by this repository: explicitly typed
classes, numeric unary expressions, compatible comparisons, and conditional
expressions. It does not add a dynamic escape hatch for the rest of Manim. The
host-runtime path lowers the same checked syntax for an installed CPython
runtime without putting Ithon's forked standard library on that interpreter's
import path.
