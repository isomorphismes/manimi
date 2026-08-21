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
- The first engine module with an Ithon implementation is
  `manimlib/utils/rate_functions.pi`. Its `.py` counterpart remains temporarily
  for Python compatibility; Ithon's finder gives the `.pi` module priority.

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

The current Ithon tree is based on CPython 3.16 development. Manimi's compiled
dependencies do not yet provide a usable 3.16 stack, so this first slice checks
Ithon source natively and compares pure behavior under the supported Python
stack. Rendering through Ithon is blocked until Ithon supplies a supported
runtime ABI or the dependency stack supports that interpreter. The foreign
Python command remains explicit in the meantime.

## Ithon dependency

The required Ithon work is stacked as follows:

```text
feature/pi-source-files
    -> feature/manimi-dogfood
```

`feature/manimi-dogfood` adds the smallest non-dynamic support demanded by this
repository: explicitly typed classes, numeric unary expressions, compatible
comparisons, and conditional expressions. It does not add a dynamic escape
hatch for the rest of Manim.
