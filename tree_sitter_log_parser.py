import re
import argparse

def parse_log(log_file):
    # Regular expression patterns
    error_pattern = re.compile(r'(detect_error|recover_to_previous|recover_eof|ERROR)')
    position_pattern = re.compile(r'row:(\d+), col:(\d+)')
    action_pattern = re.compile(r'(shift|reduce) (state|sym):(\d+)')
    lexed_token_pattern = re.compile(r'lexed_lookahead sym:(\S+), size:(\d+)')
    consume_char_pattern = re.compile(r"consume character:'?(.*?)'?")

    # Data storage
    errors = []
    actions = []
    tokens = []
    positions = {}
    current_row = None
    current_col = None

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Update current position
            pos_match = position_pattern.search(line)
            if pos_match:
                current_row, current_col = map(int, pos_match.groups())

            # Extract errors
            if error_pattern.search(line):
                # Get the last known position
                error_row = current_row if current_row is not None else 'Unknown'
                error_col = current_col if current_col is not None else 'Unknown'
                errors.append({
                    'line': error_row,
                    'column': error_col,
                    'message': line,
                })

            # Extract parsing actions
            action_match = action_pattern.search(line)
            if action_match:
                action, _, state = action_match.groups()
                actions.append({
                    'action': action,
                    'state': state,
                    'line': current_row,
                    'column': current_col,
                    'message': line,
                })

            # Extract consumed characters (tokens)
            consume_match = consume_char_pattern.search(line)
            if consume_match:
                char = consume_match.group(1)
                token_line = current_row if current_row is not None else 'Unknown'
                token_col = current_col if current_col is not None else 'Unknown'
                tokens.append({
                    'char': char,
                    'line': token_line,
                    'column': token_col,
                })

    return errors, actions, tokens

def display_summary(errors, actions, tokens):
    print("\nParsing Errors:")
    print("-" * 15)
    if errors:
        for idx, error in enumerate(errors, 1):
            print(f"{idx}. Error at Line {error['line']}, Column {error['column']}:")
            print(f"   {error['message']}")
    else:
        print("No errors found.")

    print("\nParsing Actions (Last 10):")
    print("-" * 25)
    for action in actions[-10:]:
        action_str = f"{action['action'].capitalize()} in State {action['state']} at Line {action['line']}, Column {action['column']}"
        print(action_str)

    print("\nTokens Consumed (Last 10):")
    print("-" * 25)
    for token in tokens[-10:]:
        print(f"Consumed '{token['char']}' at Line {token['line']}, Column {token['column']}")

def main():
    parser = argparse.ArgumentParser(description='Tree-sitter Log Parser')
    parser.add_argument('log_file', help='Path to the tree-sitter debug log file')
    args = parser.parse_args()

    errors, actions, tokens = parse_log(args.log_file)
    display_summary(errors, actions, tokens)

if __name__ == '__main__':
    main()
