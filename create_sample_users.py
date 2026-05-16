import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'picklesphere.settings')
django.setup()

from accounts.models import User

# Create sample users
users_data = [
    {
        'username': 'admin_user',
        'password': 'admin123',
        'email': 'admin@picklesphere.com',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Admin',
        'last_name': 'User'
    },
    {
        'username': 'staff_user',
        'password': 'staff123',
        'email': 'staff@picklesphere.com',
        'role': 'staff',
        'is_staff': True,
        'is_superuser': False,
        'first_name': 'Staff',
        'last_name': 'User'
    },
    {
        'username': 'regular_user',
        'password': 'user123',
        'email': 'user@picklesphere.com',
        'role': 'user',
        'is_staff': False,
        'is_superuser': False,
        'first_name': 'Regular',
        'last_name': 'User'
    }
]

for user_data in users_data:
    username = user_data['username']
    password = user_data['password']
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists. Skipping...")
        continue
    
    # Create user
    user = User.objects.create_user(
        username=username,
        password=password,
        email=user_data['email'],
        role=user_data['role'],
        is_staff=user_data['is_staff'],
        is_superuser=user_data['is_superuser'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name']
    )
    
    print(f"Created {user_data['role'].capitalize()} user: {username}")

print("\nSample users created successfully!")
print("\nLogin credentials:")
print("=" * 50)
for user_data in users_data:
    print(f"\n{user_data['role'].capitalize()} User:")
    print(f"  Username: {user_data['username']}")
    print(f"  Password: {user_data['password']}")
print("=" * 50)
