import sys
from engine_cli.manager import cmd_go, cmd_status, cmd_doctor


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: pathly <command> [args]")
        print("Commands: go <intent>  |  status [feature]  |  doctor")
        sys.exit(1)

    command = args[0]

    if command == "go":
        if len(args) < 2:
            print('Usage: pathly go "<intent>"')
            sys.exit(1)
        cmd_go(args[1])
    elif command == "status":
        cmd_status(args[1] if len(args) > 1 else None)
    elif command == "doctor":
        cmd_doctor()
    else:
        print(f"Unknown command: {command}")
        print("Commands: go <intent>  |  status [feature]  |  doctor")
        sys.exit(1)


if __name__ == "__main__":
    main()

