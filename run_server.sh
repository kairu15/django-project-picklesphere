#!/bin/bash
# PickleSphere - Start Django dev server with SMTP email support
# Run this script instead of 'python manage.py runserver'

export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST_USER="kylleacibron@gmail.com"
export EMAIL_HOST_PASSWORD="swve zura tpzq kjme"
export DEFAULT_FROM_EMAIL="kylleacibron@gmail.com"
export DEFAULT_FROM_NAME="PickleSphere"
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"

echo "🚀 Starting PickleSphere with SMTP email support..."
echo "   Email: kylleacibron@gmail.com"
echo "   SMTP:  smtp.gmail.com:587 (TLS)"
echo ""
python manage.py runserver 0.0.0.0:8000
