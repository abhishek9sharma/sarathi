import os
import json
from sarathi.llm.tool_library import (
    read_file,
    run_command,
    get_git_status,
    write_file,
    list_files,
    find_python_files,
)


def test_security():
    print("Testing read_file on .env...")
    res = read_file(".env")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting read_file on subdir/.env...")
    res = read_file("config/.env")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting write_file on .env...")
    res = write_file(".env", "SECRET=123")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting run_command with 'env'...")
    res = run_command("env")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting run_command with 'cat .env'...")
    res = run_command("cat .env")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting run_command with 'printenv'...")
    res = run_command("printenv")
    print(f"Result: {res}")
    assert "prohibited" in res.lower()

    print("\nTesting run_command safe command...")
    res = run_command("ls")
    print(f"Result: {res}")
    assert "prohibited" not in res.lower()

    # Create dummy .env for listing tests (via OS, not tool)
    with open(".env.test_secret", "w") as f:
        f.write("SECRET=123")

    print("\nTesting list_files filtering...")
    res_json = list_files(".")
    res = json.loads(res_json)
    print(f"Files found: {res}")
    assert ".env.test_secret" not in res

    print("\nTesting find_python_files filtering...")
    # Create dummy .env.py (though it's unlikely, let's check prefix/substring)
    with open("secret.env.py", "w") as f:
        f.write("print('secret')")

    res_json = find_python_files(".")
    res = json.loads(res_json)
    print(f"Python files found: {res}")
    assert "secret.env.py" not in res

    # Cleanup
    os.remove(".env.test_secret")
    os.remove("secret.env.py")

    print("\nSecurity tests passed!")


if __name__ == "__main__":
    test_security()
