import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)  # her çalıştırmada aynı veri


# VERİTABANI BAĞLANTI

conn = sqlite3.connect("subscription.db")
cursor = conn.cursor()


cursor.executescript("""
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS plans;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS usage_logs;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    signup_date DATE,
    country TEXT
);

CREATE TABLE plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT,
    monthly_price REAL
);

CREATE TABLE subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plan_id INTEGER,
    start_date DATE,
    end_date DATE,
    status TEXT
);

CREATE TABLE usage_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    usage_date DATE,
    minutes_used INTEGER
);
""")


plans = [
    ("Basic", 100),
    ("Standard", 150),
    ("Premium", 250)
]

cursor.executemany("INSERT INTO plans (plan_name, monthly_price) VALUES (?,?)", plans)

countries = ["Turkey", "Germany", "USA", "France"]

for i in range(200):
    signup = datetime.now() - timedelta(days=random.randint(30, 365))
    cursor.execute("""
        INSERT INTO users (name,email,signup_date,country)
        VALUES (?,?,?,?)
    """, (
        f"user{i}",
        f"user{i}@mail.com",
        signup.date().isoformat(),
        random.choice(countries)
    ))


for user_id in range(1, 201):
    plan_id = random.randint(1, 3)
    start = datetime.now() - timedelta(days=random.randint(30, 365))

    if random.random() < 0.2:  # %20 iptal
        end = start + timedelta(days=random.randint(30, 200))
        status = "cancelled"
    else:
        end = None
        status = "active"

    cursor.execute("""
        INSERT INTO subscriptions (user_id,plan_id,start_date,end_date,status)
        VALUES (?,?,?,?,?)
    """, (user_id, plan_id, start.date().isoformat(),
          end.date().isoformat() if end else None, status))


# Kullanıcı davranış profilleri:
#  - %10 "pasif": son 30 gündür hiç kullanmıyor
#  - %15 "düşüşte": son 14 günde kullanımı %80+ azalmış (churn adayı)
#  - geri kalanı normal kullanıcı
def gunluk_kullanim():
    rand = random.random()
    if rand < 0.1:
        return 0
    elif rand < 0.3:
        return random.randint(1, 3)
    elif rand < 0.8:
        return random.randint(10, 60)
    return random.randint(100, 180)


for user_id in range(1, 201):
    profil = random.random()
    for day in range(60):
        date = datetime.now() - timedelta(days=day)

        if profil < 0.10 and day <= 30:
            minutes = 0                                  # pasif
        elif profil < 0.25 and day < 14:
            minutes = random.randint(0, 2)               # düşüşte
        else:
            minutes = gunluk_kullanim()                  # normal

        cursor.execute("""
            INSERT INTO usage_logs (user_id,usage_date,minutes_used)
            VALUES (?,?,?)
        """, (user_id, date.date().isoformat(), minutes))

conn.commit()


query1 = """
SELECT u.user_id, u.name,
       SUM(CASE WHEN ul.usage_date >= DATE('now','-30 day')
                THEN ul.minutes_used ELSE 0 END) as last30
FROM users u
JOIN subscriptions s ON u.user_id = s.user_id
LEFT JOIN usage_logs ul ON u.user_id = ul.user_id
WHERE s.status = 'active'
GROUP BY u.user_id
HAVING last30 = 0;
"""

df_inactive = pd.read_sql_query(query1, conn)

print("\nAktif ama kullanmayan kullanıcı sayısı:")
print(len(df_inactive))


# ANALİZ 2: CHURN ADAYLARI (%80 DÜŞÜŞ)

query2 = """
WITH usage_compare AS (
SELECT u.user_id,
SUM(CASE WHEN ul.usage_date >= DATE('now','-14 day')
         THEN ul.minutes_used ELSE 0 END) as last14,
SUM(CASE WHEN ul.usage_date BETWEEN DATE('now','-28 day') 
         AND DATE('now','-15 day')
         THEN ul.minutes_used ELSE 0 END) as prev14
FROM users u
JOIN usage_logs ul ON u.user_id = ul.user_id
GROUP BY u.user_id
)
SELECT *,
CASE WHEN prev14 > 0
     THEN (prev14 - last14) * 1.0 / prev14
     ELSE 0 END as drop_ratio
FROM usage_compare
WHERE prev14 > 0
AND ((prev14 - last14) * 1.0 / prev14) >= 0.8;
"""

df_churn = pd.read_sql_query(query2, conn)

print("\nChurn adayı sayısı:")
print(len(df_churn))


# ANALİZ 3: LTV HESABI

query3 = """
SELECT u.user_id,
       p.monthly_price,
       (julianday(COALESCE(s.end_date, DATE('now'))) - 
        julianday(s.start_date)) / 30.0 as months,
       p.monthly_price *
       ((julianday(COALESCE(s.end_date, DATE('now'))) - 
         julianday(s.start_date)) / 30.0) as LTV
FROM users u
JOIN subscriptions s ON u.user_id = s.user_id
JOIN plans p ON s.plan_id = p.plan_id;
"""

df_ltv = pd.read_sql_query(query3, conn)

print("\nEn değerli 10 kullanıcı:")
print(df_ltv.sort_values("LTV", ascending=False).head(10))


print("\nEn riskli 10 kullanıcı:")
print(df_churn.sort_values("drop_ratio", ascending=False).head(10))

conn.close()

