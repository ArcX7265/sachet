"""Run from services/api: python -m app.manage migrate|account|disable."""
import argparse
import getpass
from .accounts import provision, disable


def main():
    parser = argparse.ArgumentParser(description="Sachet database and pilot account administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    account = commands.add_parser("account")
    account.add_argument("username")
    account.add_argument("--role", choices=["user", "analyst", "admin"], default="user")
    commands.add_parser("disable").add_argument("username")
    args = parser.parse_args()
    try:
        if args.command == "migrate":
            from .main import init_db
            init_db()
            print("Database schema is ready.")
        elif args.command == "account":
            password = getpass.getpass("Password (at least 12 characters): ")
            if password != getpass.getpass("Confirm password: "):
                parser.error("Passwords do not match.")
            provision(args.username, args.role, password)
            print("Account saved. Previous sessions have been revoked.")
        else:
            disable(args.username)
            print("Account disabled and sessions revoked.")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
