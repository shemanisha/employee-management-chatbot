from pwdlib import PasswordHash


# Password we want to use for testing
password = "Password@123"


# Convert the password from string to bytes
password_bytes = password.encode("utf-8")


password_hash = PasswordHash.recommended()
hashed_password = password_hash.hash(password)


print("Password:")
print(password)

print("\nHashed Password:")
print(hashed_password)