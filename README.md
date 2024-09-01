# tree-sitter-al
[tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for AL

This is a work in progress. The parser is not complete and may not work as expected.
You can test it on your own AL files by running the parse command.

## Installation
Clone the repository and install the dependencies with npm.
```bash
npm install
```

## Build
```bash
npm run build
```

## Test
The tests are incomplete and may not work as expected. Ignore them for now.
```bash
npm run test
```

## Parse
```bash
npm run parse <path-to-al-file>
```

## Parse and debug
Send the debug flag to see the parsed tree. This is useful for debugging the parser. Please add the output to issues if you find any bugs. I might need the original AL file to debug the issue, but just the debug output is enough as a start.
```bash
tree-sitter parse <path-to-al-file> --debug
```

References
- [AL Language Spec](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-dev-overview)
