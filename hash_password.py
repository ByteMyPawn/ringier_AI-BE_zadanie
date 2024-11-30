from passlib.context import CryptContext


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Create a CryptContext object
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password to hash
password = "ComplicatedPassword".encode('utf-8')

# Generate the hashed password
hashed_password = pwd_context.hash(password)

print(f"Hashed password: {hashed_password}")
