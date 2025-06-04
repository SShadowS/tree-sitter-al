The following is a complete list of built-in functions you can use in your `grammar.js` to define rules. Use-cases for some of these functions will be explained in more detail in later sections.

*   **Symbols (the `$` object)** - Every grammar rule is written as a JavaScript function that takes a parameter conventionally called `$`. The syntax `$.identifier` is how you refer to another grammar symbol within a rule. Names starting with `$.MISSING` or `$.UNEXPECTED` should be avoided as they have special meaning for the `tree-sitter test` command.
*   **String and Regex literals** - The terminal symbols in a grammar are described using JavaScript strings and regular expressions. Of course during parsing, Tree-sitter does not actually use JavaScript’s regex engine to evaluate these regexes; it generates its own regex-matching logic as part of each parser. Regex literals are just used as a convenient way of writing regular expressions in your grammar.
*   **Regex Limitations** - Currently, only a subset of the Regex engine is actually supported. This is due to certain features like lookahead and lookaround assertions not feasible to use in an LR(1) grammar, as well as certain flags being unnecessary for tree-sitter. However, plenty of features are supported by default:
    
    *   Character classes
    *   Character ranges
    *   Character sets
    *   Quantifiers
    *   Alternation
    *   Grouping
    *   Unicode character escapes
    *   Unicode property escapes
*   **Sequences : `seq(rule1, rule2, ...)`** - This function creates a rule that matches any number of other rules, one after another. It is analogous to simply writing multiple symbols next to each other in [EBNF notation](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form).
*   **Alternatives : `choice(rule1, rule2, ...)`** - This function creates a rule that matches _one_ of a set of possible rules. The order of the arguments does not matter. This is analogous to the `|` (pipe) operator in EBNF notation.
*   **Repetitions : `repeat(rule)`** - This function creates a rule that matches _zero-or-more_ occurrences of a given rule. It is analogous to the `{x}` (curly brace) syntax in EBNF notation.
*   **Repetitions : `repeat1(rule)`** - This function creates a rule that matches _one-or-more_ occurrences of a given rule. The previous `repeat` rule is implemented in terms of `repeat1` but is included because it is very commonly used.
*   **Options : `optional(rule)`** - This function creates a rule that matches _zero or one_ occurrence of a given rule. It is analogous to the `[x]` (square bracket) syntax in EBNF notation.
*   **Precedence : `prec(number, rule)`** - This function marks the given rule with a numerical precedence which will be used to resolve [_LR(1) Conflicts_](https://en.wikipedia.org/wiki/LR_parser#Conflicts_in_the_constructed_tables) at parser-generation time. When two rules overlap in a way that represents either a true ambiguity or a _local_ ambiguity given one token of lookahead, Tree-sitter will try to resolve the conflict by matching the rule with the higher precedence. The default precedence of all rules is zero. This works similarly to the [precedence directives](https://docs.oracle.com/cd/E19504-01/802-5880/6i9k05dh3/index.html) in Yacc grammars.
*   **Left Associativity : `prec.left([number], rule)`** - This function marks the given rule as left-associative (and optionally applies a numerical precedence). When an LR(1) conflict arises in which all of the rules have the same numerical precedence, Tree-sitter will consult the rules’ associativity. If there is a left-associative rule, Tree-sitter will prefer matching a rule that ends _earlier_. This works similarly to [associativity directives](https://docs.oracle.com/cd/E19504-01/802-5880/6i9k05dh3/index.html) in Yacc grammars.
*   **Right Associativity : `prec.right([number], rule)`** - This function is like `prec.left`, but it instructs Tree-sitter to prefer matching a rule that ends _later_.
*   **Dynamic Precedence : `prec.dynamic(number, rule)`** - This function is similar to `prec`, but the given numerical precedence is applied at _runtime_ instead of at parser generation time. This is only necessary when handling a conflict dynamically using the `conflicts` field in the grammar, and when there is a genuine _ambiguity_: multiple rules correctly match a given piece of code. In that event, Tree-sitter compares the total dynamic precedence associated with each rule, and selects the one with the highest total. This is similar to [dynamic precedence directives](https://www.gnu.org/software/bison/manual/html_node/Generalized-LR-Parsing.html) in Bison grammars.
*   **Tokens : `token(rule)`** - This function marks the given rule as producing only a single token. Tree-sitter’s default is to treat each String or RegExp literal in the grammar as a separate token. Each token is matched separately by the lexer and returned as its own leaf node in the tree. The `token` function allows you to express a complex rule using the functions described above (rather than as a single regular expression) but still have Tree-sitter treat it as a single token. The token function will only accept terminal rules, so `token($.foo)` will not work. You can think of it as a shortcut for squashing complex rules of strings or regexes down to a single token.
*   **Immediate Tokens : `token.immediate(rule)`** - Usually, whitespace (and any other extras, such as comments) is optional before each token. This function means that the token will only match if there is no whitespace.
*   **Aliases : `alias(rule, name)`** - This function causes the given rule to _appear_ with an alternative name in the syntax tree. If `name` is a _symbol_, as in `alias($.foo, $.bar)`, then the aliased rule will _appear_ as a [named node](./using-parsers#named-vs-anonymous-nodes) called `bar`. And if `name` is a _string literal_, as in `alias($.foo, 'bar')`, then the aliased rule will appear as an [anonymous node](./using-parsers#named-vs-anonymous-nodes), as if the rule had been written as the simple string.
*   **Field Names : `field(name, rule)`** - This function assigns a _field name_ to the child node(s) matched by the given rule. In the resulting syntax tree, you can then use that field name to access specific children.

In addition to the `name` and `rules` fields, grammars have a few other optional public fields that influence the behavior of the parser.

*   **`extras`** - an array of tokens that may appear _anywhere_ in the language. This is often used for whitespace and comments. The default value of `extras` is to accept whitespace. To control whitespace explicitly, specify `extras: $ => []` in your grammar.
*   **`inline`** - an array of rule names that should be automatically _removed_ from the grammar by replacing all of their usages with a copy of their definition. This is useful for rules that are used in multiple places but for which you _don’t_ want to create syntax tree nodes at runtime.
*   **`conflicts`** - an array of arrays of rule names. Each inner array represents a set of rules that’s involved in an _LR(1) conflict_ that is _intended to exist_ in the grammar. When these conflicts occur at runtime, Tree-sitter will use the GLR algorithm to explore all of the possible interpretations. If _multiple_ parses end up succeeding, Tree-sitter will pick the subtree whose corresponding rule has the highest total _dynamic precedence_.
*   **`externals`** - an array of token names which can be returned by an [_external scanner_](#external-scanners). External scanners allow you to write custom C code which runs during the lexing process in order to handle lexical rules (e.g. Python’s indentation tokens) that cannot be described by regular expressions.
*   **`precedences`** - an array of array of strings, where each array of strings defines named precedence levels in descending order. These names can be used in the `prec` functions to define precedence relative only to other names in the array, rather than globally. Can only be used with parse precedence, not lexical precedence.
*   **`word`** - the name of a token that will match keywords for the purpose of the [keyword extraction](#keyword-extraction) optimization.
*   **`supertypes`** an array of hidden rule names which should be considered to be ‘supertypes’ in the generated [_node types_ file](./using-parsers#static-node-types).

Writing the Grammar
-------------------

Writing a grammar requires creativity. There are an infinite number of CFGs (context-free grammars) that can be used to describe any given language. In order to produce a good Tree-sitter parser, you need to create a grammar with two important properties:

1.  **An intuitive structure** - Tree-sitter’s output is a [concrete syntax tree](https://en.wikipedia.org/wiki/Parse_tree); each node in the tree corresponds directly to a [terminal or non-terminal symbol](https://en.wikipedia.org/wiki/Terminal_and_nonterminal_symbols) in the grammar. So in order to produce an easy-to-analyze tree, there should be a direct correspondence between the symbols in your grammar and the recognizable constructs in the language. This might seem obvious, but it is very different from the way that context-free grammars are often written in contexts like [language specifications](https://en.wikipedia.org/wiki/Programming_language_specification) or [Yacc](https://en.wikipedia.org/wiki/Yacc)/[Bison](https://en.wikipedia.org/wiki/GNU_bison) parsers.
    
2.  **A close adherence to LR(1)** - Tree-sitter is based on the [GLR parsing](https://en.wikipedia.org/wiki/GLR_parser) algorithm. This means that while it can handle any context-free grammar, it works most efficiently with a class of context-free grammars called [LR(1) Grammars](https://en.wikipedia.org/wiki/LR_parser). In this respect, Tree-sitter’s grammars are similar to (but less restrictive than) [Yacc](https://en.wikipedia.org/wiki/Yacc) and [Bison](https://en.wikipedia.org/wiki/GNU_bison) grammars, but _different_ from [ANTLR grammars](https://www.antlr.org), [Parsing Expression Grammars](https://en.wikipedia.org/wiki/Parsing_expression_grammar), or the [ambiguous grammars](https://en.wikipedia.org/wiki/Ambiguous_grammar) commonly used in language specifications.
    

It’s unlikely that you’ll be able to satisfy these two properties just by translating an existing context-free grammar directly into Tree-sitter’s grammar format. There are a few kinds of adjustments that are often required. The following sections will explain these adjustments in more depth.

### The First Few Rules

It’s usually a good idea to find a formal specification for the language you’re trying to parse. This specification will most likely contain a context-free grammar. As you read through the rules of this CFG, you will probably discover a complex and cyclic graph of relationships. It might be unclear how you should navigate this graph as you define your grammar.

Although languages have very different constructs, their constructs can often be categorized in to similar groups like _Declarations_, _Definitions_, _Statements_, _Expressions_, _Types_, and _Patterns_. In writing your grammar, a good first step is to create just enough structure to include all of these basic _groups_ of symbols. For a language like Go, you might start with something like this:

    {
      // ...
    
      rules: {
        source_file: $ => repeat($._definition),
    
        _definition: $ => choice(
          $.function_definition
          // TODO: other kinds of definitions
        ),
    
        function_definition: $ => seq(
          'func',
          $.identifier,
          $.parameter_list,
          $._type,
          $.block
        ),
    
        parameter_list: $ => seq(
          '(',
           // TODO: parameters
          ')'
        ),
    
        _type: $ => choice(
          'bool'
          // TODO: other kinds of types
        ),
    
        block: $ => seq(
          '{',
          repeat($._statement),
          '}'
        ),
    
        _statement: $ => choice(
          $.return_statement
          // TODO: other kinds of statements
        ),
    
        return_statement: $ => seq(
          'return',
          $._expression,
          ';'
        ),
    
        _expression: $ => choice(
          $.identifier,
          $.number
          // TODO: other kinds of expressions
        ),
    
        identifier: $ => /[a-z]+/,
    
        number: $ => /\d+/
      }
    }
    

Some of the details of this grammar will be explained in more depth later on, but if you focus on the `TODO` comments, you can see that the overall strategy is _breadth-first_. Notably, this initial skeleton does not need to directly match an exact subset of the context-free grammar in the language specification. It just needs to touch on the major groupings of rules in as simple and obvious a way as possible.

With this structure in place, you can now freely decide what part of the grammar to flesh out next. For example, you might decide to start with _types_. One-by-one, you could define the rules for writing basic types and composing them into more complex types:

    {
      // ...
    
      _type: $ => choice(
        $.primitive_type,
        $.array_type,
        $.pointer_type
      ),
    
      primitive_type: $ => choice(
        'bool',
        'int'
      ),
    
      array_type: $ => seq(
        '[',
        ']',
        $._type
      ),
    
      pointer_type: $ => seq(
        '*',
        $._type
      )
    }
    

After developing the _type_ sublanguage a bit further, you might decide to switch to working on _statements_ or _expressions_ instead. It’s often useful to check your progress by trying to parse some real code using `tree-sitter parse`.

**And remember to add tests for each rule in your `test/corpus` folder!**

### Structuring Rules Well

Imagine that you were just starting work on the [Tree-sitter JavaScript parser](https://github.com/tree-sitter/tree-sitter-javascript). Naively, you might try to directly mirror the structure of the [ECMAScript Language Spec](https://262.ecma-international.org/6.0/). To illustrate the problem with this approach, consider the following line of code:

    return x + y;
    

According to the specification, this line is a `ReturnStatement`, the fragment `x + y` is an `AdditiveExpression`, and `x` and `y` are both `IdentifierReferences`. The relationship between these constructs is captured by a complex series of production rules:

    ReturnStatement          ->  'return' Expression
    Expression               ->  AssignmentExpression
    AssignmentExpression     ->  ConditionalExpression
    ConditionalExpression    ->  LogicalORExpression
    LogicalORExpression      ->  LogicalANDExpression
    LogicalANDExpression     ->  BitwiseORExpression
    BitwiseORExpression      ->  BitwiseXORExpression
    BitwiseXORExpression     ->  BitwiseANDExpression
    BitwiseANDExpression     ->  EqualityExpression
    EqualityExpression       ->  RelationalExpression
    RelationalExpression     ->  ShiftExpression
    ShiftExpression          ->  AdditiveExpression
    AdditiveExpression       ->  MultiplicativeExpression
    MultiplicativeExpression ->  ExponentiationExpression
    ExponentiationExpression ->  UnaryExpression
    UnaryExpression          ->  UpdateExpression
    UpdateExpression         ->  LeftHandSideExpression
    LeftHandSideExpression   ->  NewExpression
    NewExpression            ->  MemberExpression
    MemberExpression         ->  PrimaryExpression
    PrimaryExpression        ->  IdentifierReference
    

The language spec encodes the twenty different precedence levels of JavaScript expressions using twenty levels of indirection between `IdentifierReference` and `Expression`. If we were to create a concrete syntax tree representing this statement according to the language spec, it would have twenty levels of nesting, and it would contain nodes with names like `BitwiseXORExpression`, which are unrelated to the actual code.

### Using Precedence

To produce a readable syntax tree, we’d like to model JavaScript expressions using a much flatter structure like this:

    {
      // ...
    
      _expression: $ => choice(
        $.identifier,
        $.unary_expression,
        $.binary_expression,
        // ...
      ),
    
      unary_expression: $ => choice(
        seq('-', $._expression),
        seq('!', $._expression),
        // ...
      ),
    
      binary_expression: $ => choice(
        seq($._expression, '*', $._expression),
        seq($._expression, '+', $._expression),
        // ...
      ),
    }
    

Of course, this flat structure is highly ambiguous. If we try to generate a parser, Tree-sitter gives us an error message:

    Error: Unresolved conflict for symbol sequence:
    
      '-'  _expression  •  '*'  …
    
    Possible interpretations:
    
      1:  '-'  (binary_expression  _expression  •  '*'  _expression)
      2:  (unary_expression  '-'  _expression)  •  '*'  …
    
    Possible resolutions:
    
      1:  Specify a higher precedence in `binary_expression` than in the other rules.
      2:  Specify a higher precedence in `unary_expression` than in the other rules.
      3:  Specify a left or right associativity in `unary_expression`
      4:  Add a conflict for these rules: `binary_expression` `unary_expression`
    

Note: The • character in the error message indicates where exactly during parsing the conflict occurs, or in other words, where the parser is encountering ambiguity.

For an expression like `-a * b`, it’s not clear whether the `-` operator applies to the `a * b` or just to the `a`. This is where the `prec` function [described above](#the-grammar-dsl) comes into play. By wrapping a rule with `prec`, we can indicate that certain sequence of symbols should _bind to each other more tightly_ than others. For example, the `'-', $._expression` sequence in `unary_expression` should bind more tightly than the `$._expression, '+', $._expression` sequence in `binary_expression`:

    {
      // ...
    
      unary_expression: $ => prec(2, choice(
        seq('-', $._expression),
        seq('!', $._expression),
        // ...
      ))
    }
    

### Using Associativity

Applying a higher precedence in `unary_expression` fixes that conflict, but there is still another conflict:

    Error: Unresolved conflict for symbol sequence:
    
      _expression  '*'  _expression  •  '*'  …
    
    Possible interpretations:
    
      1:  _expression  '*'  (binary_expression  _expression  •  '*'  _expression)
      2:  (binary_expression  _expression  '*'  _expression)  •  '*'  …
    
    Possible resolutions:
    
      1:  Specify a left or right associativity in `binary_expression`
      2:  Add a conflict for these rules: `binary_expression`
    

For an expression like `a * b * c`, it’s not clear whether we mean `a * (b * c)` or `(a * b) * c`. This is where `prec.left` and `prec.right` come into use. We want to select the second interpretation, so we use `prec.left`.

    {
      // ...
    
      binary_expression: $ => choice(
        prec.left(2, seq($._expression, '*', $._expression)),
        prec.left(1, seq($._expression, '+', $._expression)),
        // ...
      ),
    }
    

### Hiding Rules

You may have noticed in the above examples that some of the grammar rule name like `_expression` and `_type` began with an underscore. Starting a rule’s name with an underscore causes the rule to be _hidden_ in the syntax tree. This is useful for rules like `_expression` in the grammars above, which always just wrap a single child node. If these nodes were not hidden, they would add substantial depth and noise to the syntax tree without making it any easier to understand.

### Using Fields

Often, it’s easier to analyze a syntax node if you can refer to its children by _name_ instead of by their position in an ordered list. Tree-sitter grammars support this using the `field` function. This function allows you to assign unique names to some or all of a node’s children:

    function_definition: $ => seq(
      'func',
      field('name', $.identifier),
      field('parameters', $.parameter_list),
      field('return_type', $._type),
      field('body', $.block)
    )
    

Adding fields like this allows you to retrieve nodes using the [field APIs](./using-parsers#node-field-names).

Lexical Analysis
----------------

Tree-sitter’s parsing process is divided into two phases: parsing (which is described above) and [lexing](https://en.wikipedia.org/wiki/Lexical_analysis) - the process of grouping individual characters into the language’s fundamental _tokens_. There are a few important things to know about how Tree-sitter’s lexing works.

### Conflicting Tokens

Grammars often contain multiple tokens that can match the same characters. For example, a grammar might contain the tokens (`"if"` and `/[a-z]+/`). Tree-sitter differentiates between these conflicting tokens in a few ways.

1.  **Context-aware Lexing** - Tree-sitter performs lexing on-demand, during the parsing process. At any given position in a source document, the lexer only tries to recognize tokens that are _valid_ at that position in the document.
    
2.  **Lexical Precedence** - When the precedence functions described [above](#the-grammar-dsl) are used _within_ the `token` function, the given explicit precedence values serve as instructions to the lexer. If there are two valid tokens that match the characters at a given position in the document, Tree-sitter will select the one with the higher precedence.
    
3.  **Match Length** - If multiple valid tokens with the same precedence match the characters at a given position in a document, Tree-sitter will select the token that matches the [longest sequence of characters](https://en.wikipedia.org/wiki/Maximal_munch).
    
4.  **Match Specificity** - If there are two valid tokens with the same precedence and which both match the same number of characters, Tree-sitter will prefer a token that is specified in the grammar as a `String` over a token specified as a `RegExp`.
    
5.  **Rule Order** - If none of the above criteria can be used to select one token over another, Tree-sitter will prefer the token that appears earlier in the grammar.
    

If there is an external scanner it may have [an additional impact](#other-external-scanner-details) over regular tokens defined in the grammar.

### Lexical Precedence vs. Parse Precedence

One common mistake involves not distinguishing _lexical precedence_ from _parse precedence_. Parse precedence determines which rule is chosen to interpret a given sequence of tokens. _Lexical precedence_ determines which token is chosen to interpret at a given position of text and it is a lower-level operation that is done first. The above list fully captures Tree-sitter’s lexical precedence rules, and you will probably refer back to this section of the documentation more often than any other. Most of the time when you really get stuck, you’re dealing with a lexical precedence problem. Pay particular attention to the difference in meaning between using `prec` inside of the `token` function versus outside of it. The _lexical precedence_ syntax is `token(prec(N, ...))`.

### Keywords

Many languages have a set of _keyword_ tokens (e.g. `if`, `for`, `return`), as well as a more general token (e.g. `identifier`) that matches any word, including many of the keyword strings. For example, JavaScript has a keyword `instanceof`, which is used as a binary operator, like this:

    if (a instanceof Something) b();
    

The following, however, is not valid JavaScript:

    if (a instanceofSomething) b();
    

A keyword like `instanceof` cannot be followed immediately by another letter, because then it would be tokenized as an `identifier`, **even though an identifier is not valid at that position**. Because Tree-sitter uses context-aware lexing, as described [above](#conflicting-tokens), it would not normally impose this restriction. By default, Tree-sitter would recognize `instanceofSomething` as two separate tokens: the `instanceof` keyword followed by an `identifier`.

### Keyword Extraction

Fortunately, Tree-sitter has a feature that allows you to fix this, so that you can match the behavior of other standard parsers: the `word` token. If you specify a `word` token in your grammar, Tree-sitter will find the set of _keyword_ tokens that match strings also matched by the `word` token. Then, during lexing, instead of matching each of these keywords individually, Tree-sitter will match the keywords via a two-step process where it _first_ matches the `word` token.

For example, suppose we added `identifier` as the `word` token in our JavaScript grammar:

    grammar({
      name: 'javascript',
    
      word: $ => $.identifier,
    
      rules: {
        _expression: $ => choice(
          $.identifier,
          $.unary_expression,
          $.binary_expression
          // ...
        ),
    
        binary_expression: $ => choice(
          prec.left(1, seq($._expression, 'instanceof', $._expression))
          // ...
        ),
    
        unary_expression: $ => choice(
          prec.left(2, seq('typeof', $._expression))
          // ...
        ),
    
        identifier: $ => /[a-z_]+/
      }
    });
    

Tree-sitter would identify `typeof` and `instanceof` as keywords. Then, when parsing the invalid code above, rather than scanning for the `instanceof` token individually, it would scan for an `identifier` first, and find `instanceofSomething`. It would then correctly recognize the code as invalid.

Aside from improving error detection, keyword extraction also has performance benefits. It allows Tree-sitter to generate a smaller, simpler lexing function, which means that **the parser will compile much more quickly**.