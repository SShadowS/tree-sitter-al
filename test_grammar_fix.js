// Grammar fix test
module.exports = grammar({
  name: 'test',
  
  rules: {
    source_file: $ => $.expression,
    
    expression: $ => choice(
      $.qualified_enum,
      $.quoted_identifier,
      $.identifier
    ),
    
    // Key fix: higher precedence for qualified_enum
    qualified_enum: $ => prec(100, seq(
      field('enum_type', choice(
        $.quoted_identifier,
        $.identifier
      )),
      '::',
      field('value', $.identifier)
    )),
    
    quoted_identifier: $ => seq(
      '"',
      /[^"]+/,
      '"'
    ),
    
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/
  }
});