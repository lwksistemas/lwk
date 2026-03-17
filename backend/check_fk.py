import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute("""
        SELECT tc.constraint_name, rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.referential_constraints rc 
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.table_name = 'superadmin_financeiroloja'
        AND tc.constraint_type = 'FOREIGN KEY';
    """)
    for row in c.fetchall():
        print(f"Constraint: {row[0]}, Delete Rule: {row[1]}")
