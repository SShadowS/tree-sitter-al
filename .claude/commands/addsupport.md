Add support for parsing this file: $ARGUMENTS.

Follow these steps:

1. Use the `tree-sitter parse FILEPATH` command to generate the expected parse tree for the file.
2. Read the generated parse tree and identify the grammar rules that need to be added or modified.
 - Can use `tree-sitter parse --debug` to troubleshoot parsing issues
 - Look for patterns that are not currently supported in the grammar
 - For example, if the file contains a new type of object or a new syntax construct, you will need to add rules for that.
4. Edit the grammar file located at `src/grammar.js` to include the necessary rules.
5. Edit the grammar file to include the necessary rules.
6. Create a new test file in the `test/corpus/` directory with tests for the patterns added support for.
7. Run `tree-sitter generate` to update the parser.
8. Run `tree-sitter test` to validate the new grammar rules against the test cases.
9. If the tests pass, commit the changes with a message of what was added or fixed.

- Keep tests comprehensive to cover edge cases
A file is never done until it has been tested against the grammar and ALL tests have passed. So requires a `tree-sitter generate && tree-sitter test` to ensure the grammar is correct and the parser works as expected.

## Resources
[tree-sitter documentation](https://tree-sitter.github.io/tree-sitter/)
[AL language reference](https://docs.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-al-language-reference)

