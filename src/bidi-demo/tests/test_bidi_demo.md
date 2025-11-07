# Test prompt for Claude Code

## Test procedure

1. Kill all processes running on port 8000
2. Create a working directory under `/tmp/test_<timestamp>`
3. Prompt user for `.env` variable values if absent
4. Copy `src/bidi-demo/**` to the working directory
5. Follow `README.md` to set up the server. Prompt user for the .env variables. Then start the server in the background mode and ask user to type `ctrl+b`
6. Once the server is ready, let the user testing it with browser for text and voice
7. Check the server log to see if the text and voice messages are handled correctly. If needed, fix the code in the working directory
8. After confirming the expected behavior, apply the fixes on the code to the `src/bidi-demo` too.
9. Write a `test_log_<timestamp>.md` to `src/bidi-demo/tests` directory with the actual procedures, outcomes, errors or frictions, or possible improvement points for the entire process.
ure
