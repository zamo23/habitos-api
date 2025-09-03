from flask_sqlalchemy import SQLAlchemy

# Inicializar SQLAlchemy
db = SQLAlchemy()

# Importar todos los modelos para hacerlos disponibles desde el paquete models
from models.user import User
from models.plan import Plan, Subscription
from models.habit import Habit, HabitEntry, HabitStreak
from models.group import Group, GroupMember, GroupInvite
from models.notification import Notification
from models.coupon import Coupon  # Importar Coupon antes de payment
from models.payment import PaymentInbox, PaymentHistory