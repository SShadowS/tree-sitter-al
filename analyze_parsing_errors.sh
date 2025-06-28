#!/bin/bash

# Count total files in errors.txt
total_errors=$(wc -l < /mnt/u/git/tree-sitter-al/BC.History/errors.txt)
echo "Total files in errors.txt: $total_errors"

# Sample files and check which ones actually have ERROR nodes
actual_errors=0
sampled=0
interface_errors=0
preprocessor_errors=0
query_errors=0
report_errors=0
other_errors=0

# Take first 100 files from errors.txt for analysis
head -100 /mnt/u/git/tree-sitter-al/BC.History/errors.txt | while read file; do
    if [ -f "$file" ]; then
        sampled=$((sampled + 1))
        result=$(tree-sitter parse "$file" 2>&1)
        if echo "$result" | grep -q "ERROR"; then
            actual_errors=$((actual_errors + 1))
            
            # Categorize error types
            if [[ "$file" == *".Interface.al" ]]; then
                interface_errors=$((interface_errors + 1))
                echo "INTERFACE ERROR: $(basename "$file")"
            elif [[ "$file" == *".Query.al" ]]; then
                query_errors=$((query_errors + 1))
                echo "QUERY ERROR: $(basename "$file")"
            elif [[ "$file" == *".Report.al" ]] || [[ "$file" == *".ReportExt.al" ]]; then
                report_errors=$((report_errors + 1))
                echo "REPORT ERROR: $(basename "$file")"
            else
                # Check file content for preprocessor
                if grep -q "#if\|#else\|#endif" "$file" 2>/dev/null; then
                    preprocessor_errors=$((preprocessor_errors + 1))
                    echo "PREPROCESSOR ERROR: $(basename "$file")"
                else
                    other_errors=$((other_errors + 1))
                    echo "OTHER ERROR: $(basename "$file")"
                fi
            fi
            
            # Show first error location
            echo "$result" | grep -E "ERROR.*\[" | head -1
            echo ""
        fi
    fi
done

echo ""
echo "Summary:"
echo "Sampled: $sampled files"
echo "Files with actual ERROR nodes: $actual_errors"
echo "- Interface errors: $interface_errors"
echo "- Query errors: $query_errors"
echo "- Report errors: $report_errors"  
echo "- Preprocessor errors: $preprocessor_errors"
echo "- Other errors: $other_errors"