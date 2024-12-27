import re
import argparse

def parse_log(log_file):
    # Regular expression patterns
    error_pattern = re.compile(r'(detect_error|ERROR|recover_to_previous|recover_eof)')
    position_pattern = re.compile(r'row:(\d+), col:(\d+)')
    action_pattern = re.compile(r'(shift|reduce|accept|detect_error|recover_to_previous|recover_eof|skip_token|done|advance_to_state|start_error_recovery|reduce_using|accept_action|shift_extra)')
    lexed_token_pattern = re.compile(r'lexed_lookahead sym:([^,]+), size:(\d+)')
    consume_char_pattern = re.compile(r"consume character:(.+)")
    process_version_pattern = re.compile(r'process version:(\d+), version_count:(\d+), state:(\d+), row:(\d+), col:(\d+)')

    # Data storage
    errors = []
    parsing_steps = []
    tokens = []
    lexed_tokens = []
    current_row = None
    current_col = None

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Update current position from 'process' lines
            proc_match = process_version_pattern.search(line)
            if proc_match:
                _, _, _, current_row, current_col = proc_match.groups()
                current_row = int(current_row)
                current_col = int(current_col)

            # Update current position from 'lex_internal state' lines
            pos_match = position_pattern.search(line)
            if pos_match:
                current_row, current_col = map(int, pos_match.groups())

            # Extract errors
            if error_pattern.search(line):
                error_row = current_row if current_row is not None else 'Unknown'
                error_col = current_col if current_col is not None else 'Unknown'
                errors.append({
                    'line': error_row,
                    'column': error_col,
                    'message': line,
                })
                # Also record as a parsing step
                parsing_steps.append({
                    'action': 'Error',
                    'details': line,
                    'line': error_row,
                    'column': error_col,
                })

            # Extract parsing actions
            action_match = action_pattern.search(line)
            if action_match:
                action = action_match.group(1)
                action_line = current_row if current_row is not None else 'Unknown'
                action_col = current_col if current_col is not None else 'Unknown'
                parsing_steps.append({
                    'action': action,
                    'details': line,
                    'line': action_line,
                    'column': action_col,
                })

            # Extract lexed tokens
            lexed_match = lexed_token_pattern.search(line)
            if lexed_match:
                sym, size = lexed_match.groups()
                token_line = current_row if current_row is not None else 'Unknown'
                token_col = current_col if current_col is not None else 'Unknown'
                lexed_tokens.append({
                    'symbol': sym,
                    'size': size,
                    'line': token_line,
                    'column': token_col,
                })

            # Extract consumed characters (tokens)
            consume_match = consume_char_pattern.search(line)
            if consume_match:
                char = consume_match.group(1).strip()
                token_line = current_row if current_row is not None else 'Unknown'
                token_col = current_col if current_col is not None else 'Unknown'
                tokens.append({
                    'char': char,
                    'line': token_line,
                    'column': token_col,
                })

    return errors, parsing_steps, tokens, lexed_tokens

def display_summary(errors, parsing_steps, tokens, lexed_tokens):
    print("\nParsing Errors:")
    print("-" * 15)
    if errors:
        for idx, error in enumerate(errors, 1):
            print(f"{idx}. Error at Line {error['line']}, Column {error['column']}:")
            print(f"   {error['message']}")
    else:
        print("No errors found.")

    print("\nParsing Steps (Last 15):")
    print("-" * 25)
    for step in parsing_steps[-15:]:
        action_str = f"{step['action'].capitalize()} at Line {step['line']}, Column {step['column']}: {step['details']}"
        print(action_str)

    print("\nTokens Lexed (Last 15):")
    print("-" * 25)
    for token in lexed_tokens[-15:]:
        print(f"Lexed Token '{token['symbol']}' (size: {token['size']}) at Line {token['line']}, Column {token['column']}")

    print("\nCharacters Consumed (Last 15):")
    print("-" * 30)
    for token in tokens[-15:]:
        print(f"Consumed '{token['char']}' at Line {token['line']}, Column {token['column']}")

def main():
    parser = argparse.ArgumentParser(description='Tree-sitter Log Parser')
    parser.add_argument('log_file', help='Path to the tree-sitter debug log file')
    args = parser.parse_args()

    errors, parsing_steps, tokens, lexed_tokens = parse_log(args.log_file)
    display_summary(errors, parsing_steps, tokens, lexed_tokens)

if __name__ == '__main__':
    main()
