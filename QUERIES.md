Queries
-------

Tree-sitter’s syntax highlighting system is based on _tree queries_, which are a general system for pattern-matching on Tree-sitter’s syntax trees. See [this section](./using-parsers#pattern-matching-with-queries) of the documentation for more information about tree queries.

Syntax highlighting is controlled by _three_ different types of query files that are usually included in the `queries` folder. The default names for the query files use the `.scm` file. We chose this extension because it commonly used for files written in [Scheme](https://en.wikipedia.org/wiki/Scheme_%28programming_language%29), a popular dialect of Lisp, and these query files use a Lisp-like syntax.

Alternatively, you can think of `.scm` as an acronym for “Source Code Matching”.

### Highlights

The most important query is called the highlights query. The highlights query uses _captures_ to assign arbitrary _highlight names_ to different nodes in the tree. Each highlight name can then be mapped to a color (as described [above](#theme)). Commonly used highlight names include `keyword`, `function`, `type`, `property`, and `string`. Names can also be dot-separated like `function.builtin`.

#### Example Input

For example, consider the following Go code:

    func increment(a int) int {
        return a + 1
    }
    

With this syntax tree:

    (source_file
      (function_declaration
        name: (identifier)
        parameters: (parameter_list
          (parameter_declaration
            name: (identifier)
            type: (type_identifier)))
        result: (type_identifier)
        body: (block
          (return_statement
            (expression_list
              (binary_expression
                left: (identifier)
                right: (int_literal)))))))
    

#### Example Query

Suppose we wanted to render this code with the following colors:

*   keywords `func` and `return` in purple
*   function `increment` in blue
*   type `int` in green
*   number `5` brown

We can assign each of these categories a _highlight name_ using a query like this:

    ; highlights.scm
    
    "func" @keyword
    "return" @keyword
    (type_identifier) @type
    (int_literal) @number
    (function_declaration name: (identifier) @function)
    

Then, in our config file, we could map each of these highlight names to a color:

    {
      "theme": {
        "keyword": "purple",
        "function": "blue",
        "type": "green",
        "number": "brown"
      }
    }
    

#### Result

Running `tree-sitter highlight` on this Go file would produce output like this:

func increment(a int) int {
    return a + 1
}

### Local Variables

Good syntax highlighting helps the reader to quickly distinguish between the different types of _entities_ in their code. Ideally, if a given entity appears in _multiple_ places, it should be colored the same in each place. The Tree-sitter syntax highlighting system can help you to achieve this by keeping track of local scopes and variables.

The _local variables_ query is different from the highlights query in that, while the highlights query uses _arbitrary_ capture names which can then be mapped to colors, the locals variable query uses a fixed set of capture names, each of which has a special meaning.

The capture names are as follows:

*   `@local.scope` - indicates that a syntax node introduces a new local scope.
*   `@local.definition` - indicates that a syntax node contains the _name_ of a definition within the current local scope.
*   `@local.reference` - indicates that a syntax node contains the _name_ which _may_ refer to an earlier definition within some enclosing scope.

When highlighting a file, Tree-sitter will keep track of the set of scopes that contains any given position, and the set of definitions within each scope. When processing a syntax node that is captured as a `local.reference`, Tree-sitter will try to find a definition for a name that matches the node’s text. If it finds a match, Tree-sitter will ensure that the _reference_ and the _definition_ are colored the same.

The information produced by this query can also be _used_ by the highlights query. You can _disable_ a pattern for nodes which have been identified as local variables by adding the predicate `(#is-not? local)` to the pattern. This is used in the example below:

#### Example Input

Consider this Ruby code:

    def process_list(list)
      context = current_context
      list.map do |item|
        process_item(item, context)
      end
    end
    
    item = 5
    list = [item]
    

With this syntax tree:

    (program
      (method
        name: (identifier)
        parameters: (method_parameters
          (identifier))
        (assignment
          left: (identifier)
          right: (identifier))
        (method_call
          method: (call
            receiver: (identifier)
            method: (identifier))
          block: (do_block
            (block_parameters
              (identifier))
            (method_call
              method: (identifier)
              arguments: (argument_list
                (identifier)
                (identifier))))))
      (assignment
        left: (identifier)
        right: (integer))
      (assignment
        left: (identifier)
        right: (array
          (identifier))))
    

There are several different types of names within this method:

*   `process_list` is a method.
*   Within this method, `list` is a formal parameter
*   `context` is a local variable.
*   `current_context` is _not_ a local variable, so it must be a method.
*   Within the `do` block, `item` is a formal parameter
*   Later on, `item` and `list` are both local variables (not formal parameters).

#### Example Queries

Let’s write some queries that let us clearly distinguish between these types of names. First, set up the highlighting query, as described in the previous section. We’ll assign distinct colors to method calls, method definitions, and formal parameters:

    ; highlights.scm
    
    (call method: (identifier) @function.method)
    (method_call method: (identifier) @function.method)
    
    (method name: (identifier) @function.method)
    
    (method_parameters (identifier) @variable.parameter)
    (block_parameters (identifier) @variable.parameter)
    
    ((identifier) @function.method
     (#is-not? local))
    

Then, we’ll set up a local variable query to keep track of the variables and scopes. Here, we’re indicating that methods and blocks create local _scopes_, parameters and assignments create _definitions_, and other identifiers should be considered _references_:

    ; locals.scm
    
    (method) @local.scope
    (do_block) @local.scope
    
    (method_parameters (identifier) @local.definition)
    (block_parameters (identifier) @local.definition)
    
    (assignment left:(identifier) @local.definition)
    
    (identifier) @local.reference
    

#### Result

Running `tree-sitter highlight` on this ruby file would produce output like this:

def process\_list(list)
  context \= current\_context
  list.map do |item|
    process\_item(item, context)
  end
end

item \= 5
list \= \[item\]

### Language Injection

Some source files contain code written in multiple different languages. Examples include:

*   HTML files, which can contain JavaScript inside of `<script>` tags and CSS inside of `<style>` tags
*   [ERB](https://en.wikipedia.org/wiki/ERuby) files, which contain Ruby inside of `<% %>` tags, and HTML outside of those tags
*   PHP files, which can contain HTML between the `<php` tags
*   JavaScript files, which contain regular expression syntax within regex literals
*   Ruby, which can contain snippets of code inside of heredoc literals, where the heredoc delimiter often indicates the language

All of these examples can be modeled in terms of a _parent_ syntax tree and one or more _injected_ syntax trees, which reside _inside_ of certain nodes in the parent tree. The language injection query allows you to specify these “injections” using the following captures:

*   `@injection.content` - indicates that the captured node should have its contents re-parsed using another language.
*   `@injection.language` - indicates that the captured node’s text may contain the _name_ of a language that should be used to re-parse the `@injection.content`.

The language injection behavior can also be configured by some properties associated with patterns:

*   `injection.language` - can be used to hard-code the name of a specific language.
*   `injection.combined` - indicates that _all_ of the matching nodes in the tree should have their content parsed as _one_ nested document.
*   `injection.include-children` - indicates that the `@injection.content` node’s _entire_ text should be re-parsed, including the text of its child nodes. By default, child nodes’ text will be _excluded_ from the injected document.
*   `injection.self` - indicates that the `@injection.content` node should be parsed using the same language as the node itself. This is useful for cases where the node’s language is not known until runtime (e.g. via inheriting another language)
*   `injection.parent` indicates that the `@injection.content` node should be parsed using the same language as the node’s parent language. This is only meant for injections that need to refer back to the parent language to parse the node’s text inside the injected language.

#### Examples

Consider this ruby code:

    system <<-BASH.strip!
      abc --def | ghi > jkl
    BASH
    

With this syntax tree:

    (program
      (method_call
        method: (identifier)
        arguments: (argument_list
          (call
            receiver: (heredoc_beginning)
            method: (identifier))))
      (heredoc_body
        (heredoc_end)))
    

The following query would specify that the contents of the heredoc should be parsed using a language named “BASH” (because that is the text of the `heredoc_end` node):

    (heredoc_body
      (heredoc_end) @injection.language) @injection.content
    

You can also force the language using the `#set!` predicate. For example, this will force the language to be always `ruby`.

    ((heredoc_body) @injection.content
     (#set! injection.language "ruby"))
